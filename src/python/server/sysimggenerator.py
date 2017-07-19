# -*- coding: utf-8 -*-
import OpenSSL
import getpass
import logging
import os
import re
import tarfile
import textwrap

from common.cmd import run_cmd
from server.aidecheckparser import AIDECheckParser
from server.aidecheckparser import AIDECheckParserError
from server.aidedbmanager import AIDEDatabasesManager
from server.error import ServerError
from tempfile import TemporaryFile, NamedTemporaryFile

logger = logging.getLogger(__name__)


class SystemImageGeneratorError(ServerError):
    pass


class SystemImageGenerator:
    """Generator of the reference system image that will be applied by the
       client's myscm-cli application."""

    MYSCM_IMG_FILE_NAME = "myscm-img.{}.{}.{}"
    AIDE_MIN_EXITCODE = 14  # see AIDE's manual for details about exitcodes
    IN_ARCHIVE_ADDED_DIR_NAME = "ADDED"
    IN_ARCHIVE_CHANGED_DIR_NAME = "CHANGED"
    IN_ARCHIVE_REMOVED_DIR_NAME = "REMOVED"
    # TODO add added summary text file
    REMOVED_FILES_FNAME = "removed.txt"
    CHANGED_FILES_FNAME = "changed.txt"
    SSL_CERT_DIGEST_TYPE = "sha256"

    def __init__(self, server_config):
        self.server_config = server_config
        self.aide_db_manager = AIDEDatabasesManager(server_config)
        self.client_db_path = self._get_client_db_path(server_config.options.gen_img)
        self.aide_output_parser = AIDECheckParser(
                self.client_db_path, self.server_config.aide_reference_db_path)

    def generate_img(self):
        """Generate system image file for client whose AIDE configuration is
           identified by unique client's ID `server_config.options.gen_img`
           (which is integer number) and return full path to the created system
           image."""

        system_img_path = None

        try:
            system_img_path = self._generate_img(self.client_db_path)
        except Exception as e:
            m = "Failed to generate system image based on the output of "\
                "comparison server's current configuration's state '{}' and "\
                "client's '{}' AIDE database".format(
                    self.server_config.aide_reference_db_path,
                    self.client_db_path)
            raise SystemImageGeneratorError(m, e) from e

        system_img_path = os.path.realpath(system_img_path)

        return system_img_path

    def _get_client_db_path(self, client_db_version):
        """Find and get AIDE database that client's configuration database
           version refers to."""

        if not isinstance(client_db_version, int) or client_db_version < 0:
            m = "Client's AIDE database version is expected to be " \
                "non-negative integer (current value: '{}')".format(
                    client_db_version)
            raise SystemImageGeneratorError(m)

        client_db_path = "{}.{}".format(
                  self.server_config.aide_reference_db_path, client_db_version)

        if not os.path.isfile(client_db_path):
            m = "Unrecognized client's AIDE database version '{}'. File " \
                "'{}' doesn't exist".format(client_db_version, client_db_path)
            raise SystemImageGeneratorError(m)

        logger.debug("Found client's AIDE database file '{}' that will be "
                     "used to generate system image.".format(client_db_path))

        return client_db_path

    def _generate_img(self, client_db_path):
        """Generates system image based on AIDE's --check output ran on the
           AIDE's temporary configuration file."""

        logger.info("Generating system image based on current server's "
                    "configuration and AIDE database file '{}' corresponding "
                    "to client's system configuration.".format(client_db_path))

        system_img_path = None

        with NamedTemporaryFile(mode="r+", suffix=".aide.conf") as tmp_aideconf_f:
            self._copy_aide_config_to_tmp_replacing_db_path(
                                                client_db_path, tmp_aideconf_f)

            with TemporaryFile(mode="r+", suffix=".aide.diff") as aidediff_f:
                self._save_aide_check_result_to_tmp_file(
                                                    aidediff_f, tmp_aideconf_f)
                system_img_path = self._generate_img_from_aide_check_result(
                                                                    aidediff_f)

        return system_img_path

    def _copy_aide_config_to_tmp_replacing_db_path(self, client_db_path,
                                                   tmp_aideconf_f):
        """Create temporary AIDE configuration file by copying existing one and
           assigning expected values to some variables.

           To `database` variable path to `client_db_path` database is assigned
           to be able run AIDE --check to compare current state and given state
           that corresponds to client's system configuration. Variable
           `summarize_changes` is forced to be set to `yes`."""

        aide_conf_path = self.server_config.options.AIDE_config_path

        with open(aide_conf_path) as conf_f:
            db_regex_str = r"\s*database\s*=.*\n"
            db_regex = re.compile(db_regex_str)
            new_conf_db_line = "database = file:{}\n".format(client_db_path)
            db_matches = 0

            opt_regex_str = r"\s*summarize_changes\s*=.*\n"
            opt_regex = re.compile(opt_regex_str)
            new_conf_opt_line = "summarize_changes = yes\n"
            opt_matches = 0

            for line in conf_f:
                if db_regex.fullmatch(line):
                    tmp_aideconf_f.write(new_conf_db_line)
                    db_matches += 1
                elif opt_regex.fullmatch(line):
                    tmp_aideconf_f.write(new_conf_opt_line)
                    opt_matches += 1
                else:
                    tmp_aideconf_f.write(line)

        if db_matches != 1 or opt_matches != 1:
            m = "Expected exactly one line with assignment to 'database' and "\
                "'summarize_changes' variables in '{}' AIDE's configuration "\
                "file ({} 'database' and {} 'summarize_changes' found)"\
                .format(aide_conf_path, db_matches, opt_matches)
            raise SystemImageGeneratorError(m)

    def _save_aide_check_result_to_tmp_file(self, aidediff_f, tmp_aideconf_f):
        """Save AIDE --check output to temporary file that will be processed to
           generate reference system image."""

        logger.info("Running AIDE --check. It may take some time...")

        cmd = ["aide", "--check", "-c", tmp_aideconf_f.name]
        tmp_aideconf_f.seek(0)

        # Alternatively it can be handled by using AIDE's --report option
        # instead of capturing stdout

        completed_proc = run_cmd(cmd, False, aidediff_f)

        # AIDE returns exit code to indicate whether error occured - see manual

        if completed_proc.returncode >= self.AIDE_MIN_EXITCODE:
            m = "Erroneous exitcode {} for command '{}'. Refer AIDE's manual "\
                "for details".format(completed_proc.returncode, " ".join(cmd))
            raise SystemImageGeneratorError(m)

    def _generate_img_from_aide_check_result(self, aidediff_f):
        """Read added, removed and changed entries from AIDE --check result and
           generate system image based those entries."""

        aidediff_f.seek(0)

        try:
            entries = self.aide_output_parser.read_all_entries(aidediff_f)
        except AIDECheckParserError as e:
            m = "Error occurred while parsing AIDE --check output"
            raise SystemImageGeneratorError(m, e) from e

        return self._generate_img_from_aide_entries(entries)

    def _generate_img_from_aide_entries(self, entries):
        """Generate system image based on the entries read from AIDE --check
           output."""

        # TODO begin debug to remove
        for k, v in {
                "Added entries": entries.added_entries,
                "Removed entries": entries.removed_entries,
                "Changed entries": entries.changed_entries}.items():
            print("\n{} (size: {}):\n".format(k, len(v)))
            for _, e in v.items():
                print(vars(e.aide_properties))
        # end end to remove

        img_path = self._get_img_file_full_path()

        if os.path.isfile(img_path):
            logger.warning("Overwriting '{}' system image.".format(img_path))

        with tarfile.open(img_path, "w:gz") as f:
            self._add_to_img_file_aide_added_entries(entries.added_entries, f)
            self._add_to_img_file_removed_entries(entries.removed_entries, f)
            self._add_to_img_file_changed_entries(entries.changed_entries, f)

        logger.info("Successfully created system image '{}' for client "
                    "identified by AIDE's database '{}'.".format(
                        img_path, self.client_db_path))

        img_sig_path = self._create_img_signature(img_path)

        if img_sig_path:  # if generating signature was not skipped by the user
            logger.info("Signature of the system image '{}' created "
                        "successfully!".format(img_sig_path))

        return img_path

    def _get_img_file_full_path(self):
        IMG_EXT = "tar.gz"
        FROM_DB_ID = self.server_config.options.gen_img
        TO_DB_ID = self.aide_db_manager.get_current_aide_db_number()
        FNAME = self.MYSCM_IMG_FILE_NAME.format(FROM_DB_ID, TO_DB_ID, IMG_EXT)
        return os.path.join(self.server_config.system_img_out_dir, FNAME)

    def _add_to_img_file_aide_added_entries(self, added_entries, archive_file):
        for e in added_entries.values():
            intar_path = os.path.join(self.IN_ARCHIVE_ADDED_DIR_NAME,
                                      e.aide_properties.name.lstrip(os.path.sep))
            archive_file.add(e.aide_properties.name, arcname=intar_path)

    def _add_to_img_file_removed_entries(self, removed_entries, archive_file):
        with NamedTemporaryFile(mode="r+") as tmp_removed_f:
            for r in removed_entries.values():
                line = "{}\n".format(r.aide_properties.name)
                tmp_removed_f.write(line)
            intar_path = os.path.join(self.IN_ARCHIVE_REMOVED_DIR_NAME,
                                      self.REMOVED_FILES_FNAME)
            tmp_removed_f.seek(0)
            archive_file.add(tmp_removed_f.name, arcname=intar_path)

    def _add_to_img_file_changed_entries(self, changed_entries, archive_file):
        with NamedTemporaryFile(mode="r+") as tmp_changed_f:
            for c in changed_entries.values():
                self._append_changed_entry(c, tmp_changed_f)
            intar_path = os.path.join(self.IN_ARCHIVE_CHANGED_DIR_NAME,
                                      self.CHANGED_FILES_FNAME)
            tmp_changed_f.seek(0)
            archive_file.add(tmp_changed_f.name, arcname=intar_path)

    def _append_changed_entry(self, entry, changed_f):
        properties = entry.get_aide_changed_properties()
        line = "{}\n".format(entry.aide_properties.name)
        line += "{}\n\n".format("\n".join(properties))
        changed_f.write(line)

    def _create_img_signature(self, img_path):
        priv_key_obj = self._create_priv_key_openssl_obj(img_path)

        if not priv_key_obj:
            return None

        signature = None

        with open(img_path, "rb") as img_f:
            # See: https://stackoverflow.com/q/45141917/1321680
            bytes_to_sign = img_f.read()
            signature = OpenSSL.crypto.sign(priv_key_obj, bytes_to_sign,
                                            self.SSL_CERT_DIGEST_TYPE)

        img_sig_path = "{}.sig".format(img_path)

        with open(img_sig_path, "wb") as sig_f:
            sig_f.write(signature)

        # To manually verify validity of the signature run:
        # openssl dgst -sha256 -verify cert_public_key_file.pub -signature cert_file.crt signed_file_path

        return img_sig_path

    def _create_priv_key_openssl_obj(self, img_path):
        priv_key_path = self.server_config.options.SSL_cert_priv_key_path
        pem_cert_str = self._get_priv_key_str(priv_key_path)
        priv_key = None

        while not priv_key:
            try:
                passwd = self._get_cert_password(priv_key_path, img_path)
            except KeyboardInterrupt as e:
                print()
                logger.info("Generating SSL signature for '{}' skipped by "
                            "user (keyboard interrupt).".format(img_path))
                break

            priv_key = self._get_cert_priv_key(pem_cert_str, passwd)

        return priv_key

    def _get_priv_key_str(self, priv_key_path):
        pem_cert_str = None

        try:
            with open(priv_key_path) as f:
                pem_cert_str = f.read()
        except OSError as e:
            m = "Unable to open '{}' SSL private key for certifcate for "\
                "signing system image".format(priv_key_path)
            raise SystemImageGeneratorError(m, e) from e

        return pem_cert_str

    def _get_cert_password(self, priv_key_path, img_path):
        passwd = None

        print()
        m = "Enter password protecting '{}' private key of the SSL "\
            "certificate to digitally sign system image '{}'. If you want to "\
            "skip generating SSL signature press CTRL+C (sends SIGINT "\
            "signal).".format(os.path.basename(priv_key_path),
                              os.path.basename(img_path))
        print(textwrap.fill(m, 80))
        print()

        try:
            passwd = getpass.getpass()
        except getpass.GetPassWarning:
            logger.warning("SSL certificate password input may be echoed!")

        print()

        return passwd

    def _get_cert_priv_key(self, pem_cert_str, passwd):
        CERT_FORMAT_TYPE = OpenSSL.crypto.FILETYPE_PEM
        priv_key = None

        try:
            priv_key = OpenSSL.crypto.load_privatekey(CERT_FORMAT_TYPE,
                                                      pem_cert_str,
                                                      passwd.encode("ascii"))
        except OpenSSL.crypto.Error as e:
            logger.warning("Failed to load SSL certificate private key - "
                           "check if you entered correct password")

        return priv_key
