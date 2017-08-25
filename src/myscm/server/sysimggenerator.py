# -*- coding: utf-8 -*-
import OpenSSL
import datetime
import getpass
import logging
import os
import platform
import progressbar
import re
import tarfile
import textwrap

import diff_match_patch as patcher
from tempfile import TemporaryFile, NamedTemporaryFile

import myscm.server.pkgmanager as pkgmgr
import myscm.server.scanner
from myscm.common.cmd import run_check_cmd
from myscm.server.aidecheckparser import AIDECheckParser, AIDECheckParserError
from myscm.server.aidedbmanager import AIDEDatabasesManager
from myscm.server.aideentry import AIDEEntry
from myscm.server.error import ServerError
from myscm.server.scanner import Scanner

progressbar.streams.wrap_stderr()
logger = logging.getLogger(__name__)


class SystemImageGeneratorError(ServerError):
    pass


class SystemImageGenerator:
    """Generator of the reference system image that will be applied by the
       client's myscm-cli application."""

    MYSCM_IMG_EXT = ".tar.gz"
    MYSCM_IMG_FILE_NAME = "myscm-img.{}.{}" + MYSCM_IMG_EXT
    MYSCM_IMG_FILE_NAME_REGEX = MYSCM_IMG_FILE_NAME.format(r"(\d+)", r"(\d+)")
    AIDE_MIN_EXITCODE = 14  # see AIDE's manual for details about exitcodes
    IN_ARCHIVE_ADDED_DIR_NAME = "ADDED"
    IN_ARCHIVE_CHANGED_DIR_NAME = "CHANGED"
    ADDED_FILES_FNAME = "added.txt"
    REMOVED_FILES_FNAME = "removed.txt"
    CHANGED_FILES_FNAME = "changed.txt"
    SSL_CERT_DIGEST_TYPE = "sha256"
    PATCH_EXT = ".myscmsrv-patch"
    TEMPLATE_PATH_EXT = ".myscm-template"
    TARFILE_COMPRESSION = "w:gz"
    SIGNATURE_EXT = ".sig"
    SYSTEM_STR = "System"
    LINUX_DISTRO_STR = "GNU/Linux distribution"
    CPU_ARCHITECTURE_STR = "CPU architecture"

    def __init__(self, server_config):
        self.server_config = server_config
        self.aide_db_manager = AIDEDatabasesManager(server_config)
        self.from_db_id = self.server_config.options.gen_img
        self.to_db_id = self.aide_db_manager.get_current_aide_db_number()
        self.client_db_path = self._get_client_db_path(self.from_db_id)
        self.aide_output_parser = AIDECheckParser(
                self.client_db_path, self.server_config.aide_reference_db_path)

    def generate_img(self):
        """Generate system image file for client whose AIDE configuration is
           identified by unique client's ID `server_config.options.gen_img`
           (which is integer number) and return full path to the created system
           image."""

        system_img_path = None

        if myscm.server.scanner.is_reference_aide_db_outdated(self.server_config):
            m = "Current reference AIDE database '{}' is NOT up-to-date. Run "\
                "myscm-srv with --scan option to create up-to-date aide.db "\
                "and than rerun with --gen-img.".format(
                    self.server_config.aide_reference_db_path)
            logger.info(m)
            return

        try:
            system_img_path = self._generate_img()
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

        client_db_path = self.server_config.aide_old_db_path_pattern.format(
                                          client_db_version, client_db_version)

        if not os.path.isfile(client_db_path):
            m = "Unrecognized client's AIDE database version '{}'. File " \
                "'{}' doesn't exist".format(client_db_version, client_db_path)
            raise SystemImageGeneratorError(m)

        logger.debug("Found client's AIDE database file '{}' that will be "
                     "used to generate system image.".format(client_db_path))

        return client_db_path

    def _generate_img(self):
        """Generates system image based on AIDE's --check output ran on the
           AIDE's temporary configuration file."""

        logger.info("Generating system image based on current server's "
                    "configuration and AIDE database file '{}' corresponding "
                    "to client's system configuration.".format(
                        self.client_db_path))

        system_img_path = None

        with NamedTemporaryFile(mode="r+", suffix=".aide.conf") as tmp_aideconf_f:
            self._copy_aide_config_to_tmp_replacing_db_path(tmp_aideconf_f)

            with TemporaryFile(mode="r+", suffix=".aide.diff") as aidediff_f:
                self._save_aide_check_result_to_tmp_file(aidediff_f,
                                                         tmp_aideconf_f)
                system_img_path = self._generate_img_from_aide_check_result(
                                                                    aidediff_f)

        return system_img_path

    def _copy_aide_config_to_tmp_replacing_db_path(self, tmp_aideconf_f):
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
            new_conf_db_line = "database = file:{}\n".format(self.client_db_path)
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

        aide_config_path = tmp_aideconf_f.name
        tmp_aideconf_f.seek(0)

        # Alternatively it can be handled by using AIDE's --report option
        # instead of capturing stdout

        completed_proc = run_check_cmd(aide_config_path, False, aidediff_f)

        # AIDE returns exit code to indicate whether error occured - see manual

        if completed_proc.returncode >= self.AIDE_MIN_EXITCODE:
            m = "Erroneous exitcode {} for command AIDE --check. Refer "\
                "AIDE's manual for details".format(completed_proc.returncode)
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

        img_path = self._get_img_file_full_path()

        if os.path.isfile(img_path):
            logger.warning("Overwriting '{}' system image.".format(img_path))

        with tarfile.open(img_path, self.TARFILE_COMPRESSION) as f:
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
        fname = self.MYSCM_IMG_FILE_NAME.format(self.from_db_id, self.to_db_id)
        img_out_dir = self.server_config.options.system_img_out_dir
        return os.path.join(img_out_dir, fname)

    def _add_to_img_file_aide_added_entries(self, added_entries, archive_file):
        n = len(added_entries)

        if n:
            logger.info("Adding to the system image {} new file{} that were "
                        "added to the tracked directories...".format(
                            n, "s" if n > 0 else ""))
        else:
            logger.info("No new files were added to the tracked directories, "
                        "thus no need to add any to the system image.")

        with NamedTemporaryFile(mode="r+") as tmp_added_f:
            self._append_added_entries_header(tmp_added_f)

            # Sort paths to skip e.g. /x/y/z if /x/y was already copied.

            sorted_added_entries = [e.get_full_path() for e in added_entries.values()]
            sorted_added_entries.sort()
            common_path = "/non-existing-path-to-initialize-loop"
            bar = progressbar.ProgressBar(max_value=n)

            for path in bar(sorted_added_entries):

                # Check if current file was already copied as a file contained
                # within directory that was already copied. If so, skip.

                if os.path.commonpath([path, common_path]) == common_path:
                    logger.debug("Skipping copying '{}' since it was copied "
                                 "while copying '{}'.".format(
                                    path, common_path))
                    continue

                common_path = path

                # If this file has corresponding template file, skip this file
                # because template is preferred over regular file.

                exist = self._check_if_exist_added_file_template(path)
                if exist:
                    continue

                # Get full path to file within system image (tar.gz archive).

                intar_path = self._get_added_entry_intar_path(path)

                # Make sure if file wasn't added by e.g. expanding symlinks.

                try:
                    if archive_file.getmember(intar_path):
                        logger.warning("'{}' was already added to the system "
                                       "image. Skipping.".format(intar_path))
                        continue
                except KeyError:
                    pass

                # Add recursively given file or directory filtering out files
                # that have corresponding templates.

                logger.debug("Adding {}'{}' to the system image.".format(
                             "recursively " if os.path.isdir(path) else "",
                             path))

                archive_file.add(path, arcname=intar_path,
                                 filter=self._added_files_filter)

                # Append information about current file or directory to the
                # added.txt file. Note that only top directory are appended,
                # e.g. /x/y/z will be not listed if /x/y is listed.

                self._append_added_entry_line(path, tmp_added_f)

            # Add added.txt to the system image (tar.gz archive).

            tmp_added_f.seek(0)
            archive_file.add(tmp_added_f.name, arcname=self.ADDED_FILES_FNAME)

    def _append_added_entries_header(self, f):
        title = "ADDED FILES REPORT"
        m = "This file lists files added to the myscm-srv system since '{}' "\
            "state. Detection of the added files is possible thanks to the "\
            "AIDE --check and --compare options. Current state of the system "\
            "is always stored in '{}' AIDE database file. This is result of "\
            "the comparison of those two files.".format(
                self.client_db_path, self.server_config.aide_reference_db_path)
        self._append_sys_info_header(title, m, f)
        header = "{:<100}{}\n\n".format("# name", "package")
        f.write(header)

    def _append_added_entry_line(self, path, f):
        self._append_entry_line(path, f)

    def _get_added_entry_intar_path(self, path):
        path_suffix = path.lstrip(os.path.sep)
        intar_path = os.path.join(self.IN_ARCHIVE_ADDED_DIR_NAME, path_suffix)
        return intar_path

    def _added_files_filter(self, tar_info):
        """Filter handler for TarFile.add() method."""

        # If this file has corresponding template file, skip this file
        # because template is preferred over regular file.

        exist = self._check_if_exist_added_file_template(tar_info.name)
        return None if exist else tar_info

    def _check_if_exist_changed_file_template(self, path):
        return self._check_if_exist_file_template(path, "changed")

    def _check_if_exist_added_file_template(self, path):
        return self._check_if_exist_file_template(path, "newly added")

    def _check_if_exist_file_template(self, path, ignore_str):
        if not os.path.isfile(path) or path.endswith(self.TEMPLATE_PATH_EXT):
            return False

        template_path = path + self.TEMPLATE_PATH_EXT
        template_exist = os.path.isfile(template_path)

        if template_exist:
            m = "Ignoring {} file '{}' since it has corresponding '{}' "\
                "template file. Make sure that template file is set to be "\
                "tracked by the AIDE configuration to copy it to the system "\
                "image.".format(ignore_str, path, template_path)
            logger.debug(m)

        return template_exist

    def _add_to_img_file_removed_entries(self, removed_entries, archive_file):
        n = len(removed_entries)

        if n:
            logger.info("Adding to the system image list of the {} file{} "
                        "removed from the tracked directories...".format(
                            n, "s" if n > 0 else ""))
        else:
            logger.info("No files were removed from the tracked directories, "
                        "thus list of files removed from the system is empty.")

        with NamedTemporaryFile(mode="r+") as tmp_removed_f:
            self._append_removed_entries_header(tmp_removed_f)

            # Sort paths to skip e.g. /x/y/z if /x/y was already removed.

            sorted_removed_entries = [e.get_full_path() for e in removed_entries.values()]
            sorted_removed_entries.sort()
            common_path = "/non-existing-path-to-initialize-loop"
            bar = progressbar.ProgressBar(max_value=n)

            for path in bar(sorted_removed_entries):
                self._warn_if_orphaned_template_exists(path)

                # Check if current file was already listed as removed file (as
                # a file contained within directory that was removed. If so,
                # skip.

                if os.path.commonpath([path, common_path]) == common_path:
                    logger.debug("Skipping listing removed file '{}' since it "
                                 "was listed as removed while listing removed "
                                 "'{}'.".format(path, common_path))
                    continue

                common_path = path

                # Append information about current file or directory to the
                # added.txt file. Note that only top directory are appended,
                # e.g. /x/y/z will be not listed if /x/y is listed.

                logger.debug("Adding '{}' file to the '{}' file.".format(
                             path, self.REMOVED_FILES_FNAME))

                self._append_removed_entry_line(path, tmp_removed_f)

            # Add removed.txt to the system image (tar.gz archive).

            tmp_removed_f.seek(0)
            archive_file.add(tmp_removed_f.name,
                             arcname=self.REMOVED_FILES_FNAME)

    def _append_removed_entries_header(self, f):
        title = "REMOVED FILES REPORT"
        m = "This file lists files removed from the myscm-srv system since "\
            "'{}' state. Detection of the removed files is possible thanks "\
            "to the AIDE --check and --compare options. Current state of the "\
            "system is stored in '{}' AIDE database file. This is result of "\
            "the comparison of those two files.".format(
                self.client_db_path, self.server_config.aide_reference_db_path)
        self._append_sys_info_header(title, m, f)
        header = "{:<100}{}\n\n".format("# name", "package")
        f.write(header)

    def _append_removed_entry_line(self, path, f):
        self._append_entry_line(path, f)

    def _append_entry_line(self, path, f):
        pkg_name = pkgmgr.get_file_package_name(path, self.server_config)
        line = "{:<100}{}\n".format(path + "\0", pkg_name)
        f.write(line)

    def _warn_if_orphaned_template_exists(self, path):
        template_path = path + self.TEMPLATE_PATH_EXT

        if os.path.isfile(template_path):
            m = "Orphaned template file '{}' found for corresponding removed "\
                "file '{}'. Remove it unless you need it.".format(
                    template_path, path)
            logger.warning(m)

    def _add_to_img_file_changed_entries(self, changed_entries, archive_file):
        n = len(changed_entries)

        if n:
            logger.info("Adding to the system image list of {} changed "
                        "file{} within tracked directories...".format(
                            n, "s" if n > 0 else ""))
        else:
            logger.info("No files were changed within tracked directories, "
                        "thus list of changed files that was added to the "
                        "system image is empty.")

        with NamedTemporaryFile(mode="r+") as tmp_changed_f:
            self._append_changed_entries_header(tmp_changed_f)
            bar = progressbar.ProgressBar(max_value=n)

            for c in bar(changed_entries.values()):
                path = c.get_full_path()

                # If this file has corresponding template file, skip this file
                # because template is preferred over regular file.

                exist = self._check_if_exist_changed_file_template(path)
                if exist:
                    continue

                # Append information about current file or directory to the
                # changed.txt file.

                logger.debug("Adding details of changed file '{}' to the '{}' "
                             "file.".format(path, self.CHANGED_FILES_FNAME))
                self._append_changed_entry_to_file(c, tmp_changed_f)

                # If content of the file was changed, then create patch if
                # possible. Otherwise copy whole file to the system image.

                if c.was_file_content_changed():
                    changed_path = c.get_full_path()
                    self._add_file_to_system_img_tar(changed_path,
                                                     archive_file)

            tmp_changed_f.seek(0)
            archive_file.add(tmp_changed_f.name,
                             arcname=self.CHANGED_FILES_FNAME)

    def _add_file_to_system_img_tar(self, changed_path, archive_file):
        """Add whole missing file to system image unless it's possible to
           create patch (diff) file."""

        old_changed_path = self._get_old_changed_file_version(changed_path)

        if os.path.isfile(old_changed_path):
            self._add_patch_file_to_system_img(changed_path,
                                               old_changed_path,
                                               archive_file)
        else:
            intar_path = os.path.join(self.IN_ARCHIVE_CHANGED_DIR_NAME,
                                      changed_path.lstrip(os.path.sep))

            logger.debug("Adding changed file '{}' to the system image."
                         .format(intar_path))

            archive_file.add(changed_path, arcname=intar_path)

    def _get_old_changed_file_version(self, changed_path):
        client_db_dir = os.path.dirname(self.client_db_path)
        copied_dir = os.path.join(client_db_dir, Scanner.COPIED_FILES_DIRNAME)
        return os.path.join(copied_dir, changed_path.lstrip(os.sep))

    def _add_patch_file_to_system_img(self, changed_path, old_changed_path,
                                      archive_file):
        old_txt, new_txt = None, None

        with open(old_changed_path) as old_f:
            old_txt = old_f.read()

        with open(changed_path) as new_f:
            new_txt = new_f.read()

        p = patcher.diff_match_patch()
        patch = p.patch_make(old_txt, new_txt)
        patch_text = p.patch_toText(patch)
        patch_fname = changed_path.lstrip(os.path.sep) + self.PATCH_EXT
        intar_patch_path = os.path.join(self.IN_ARCHIVE_CHANGED_DIR_NAME,
                                        patch_fname)

        with NamedTemporaryFile(mode="r+") as patch_f:
            patch_f.write(patch_text)
            patch_f.seek(0)
            archive_file.add(patch_f.name, arcname=intar_patch_path)

        logger.debug("Patch for '{}' --> '{}' saved as '{}' in '{}' system "
                     "image.".format(old_changed_path, changed_path,
                                     intar_patch_path, archive_file.name))

    def _append_changed_entries_header(self, changed_f):
        title = "MODIFIED FILES REPORT"
        m = "This file lists changes between current newest state of the "\
            "configuration of the myscm-srv machine described in '{}' AIDE "\
            "database and the old configuration '{}' that corresponds to the "\
            "client's system state which is considered to be out-of-date. "\
            "This file is sent to the client along with other files within "\
            "system image since myscm-cli needs to know which properties of "\
            "its files needs to be updated and how they should be altered. "\
            "Lines with leading '#' character are ignored. Values in "\
            "brackets next to the property values correspond to the previous "\
            "value of the file's property or to the AIDE info-character (eg. "\
            "'.' or ' ') if property was not altered (see aide.conf(5) "\
            "manual to learn more). Columns below are null separated.".format(
                self.server_config.aide_reference_db_path, self.client_db_path)

        self._append_sys_info_header(title, m, changed_f)

        names = AIDEEntry.CHANGED_FILES_HEADER_NAMES

        for h in names[:-1]:  # to skip trailing whitespaces
            changed_f.write(h.get_name())

        last_header = names[-1].get_name()
        changed_f.write(last_header.rstrip() + "\n\n")

    def _append_changed_entry_to_file(self, entry, changed_f):
        properties = entry.get_aide_changed_properties(self.server_config)
        headers = AIDEEntry.CHANGED_FILES_HEADER_NAMES

        n = len(properties)
        m = len(headers)

        if n != m:
            m = "Malformed changed files header ({} != {})".format(n, m)
            raise SystemImageGeneratorError(m)

        line = ""
        for i in range(n):
            p = properties[i]
            h = headers[i]
            line += h.formatter.format(p + "\0")

        line = line.strip()
        line = line.rstrip("\0")

        changed_f.write(line + "\n")

    def _append_sys_info_header(self, title, desc, f):
        f.write("# {}\n#\n".format(title))
        f.write(textwrap.fill(desc, width=80, initial_indent="# ",
                              subsequent_indent="# "))
        f.write("\n#\n")

        local_cur_datetime = datetime.datetime.now()
        utc_cur_datetime = datetime.datetime.utcnow()
        sys_info = [
            ["From database version", self.from_db_id],
            ["To database version", self.to_db_id],
            ["Local creation time", local_cur_datetime.strftime("%H:%M:%S")],
            ["Creation date", local_cur_datetime.strftime("%d.%m.%Y")],
            ["UTC creation time", utc_cur_datetime.strftime("%H:%M:%S")],
            ["UTC creation date", utc_cur_datetime.strftime("%d.%m.%Y")],
            [self.SYSTEM_STR, platform.system()],
            [self.LINUX_DISTRO_STR, self.server_config.distro_name.title()],
            [self.CPU_ARCHITECTURE_STR, platform.machine()],
            ["Hostname", platform.node()],
            ["Python implementation", platform.python_implementation()],
            ["Python version", platform.python_version()],
            ["Python compiler", platform.python_compiler()]
        ]

        for i in sys_info:
            k = i[0]
            v = i[1]
            f.write("# {:<24}: {}\n".format(k, v if v != "" else "?"))

        f.write("\n\n")

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

        img_sig_path = "{}{}".format(img_path, self.SIGNATURE_EXT)

        with open(img_sig_path, "wb") as sig_f:
            sig_f.write(signature)

        # To manually verify validity of the signature run:
        # openssl dgst -sha256 -verify cert_public_key_file.pub -signature cert_file.crt signed_file_path
        # TODO try: gpg --keyserver-options auto-key-retrieve --verify signed_file_path

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
            "skip generating SSL signature press CTRL+C (or send SIGINT "\
            "signal in any other way).".format(os.path.basename(priv_key_path),
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
