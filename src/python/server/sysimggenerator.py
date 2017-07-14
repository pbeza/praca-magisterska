# -*- coding: utf-8 -*-
import logging
import os
import re

from common.cmd import run_cmd
from server.aidecheckparser import AIDECheckParser
from server.aidecheckparser import AIDECheckParserError
from server.error import ServerError
from tempfile import TemporaryFile, NamedTemporaryFile

logger = logging.getLogger(__name__)


class SystemImageGeneratorError(ServerError):
    pass


class SystemImageGenerator:
    """Generator of the reference system image that will be applied by the
       client's myscm-cli application."""

    AIDE_MIN_EXITCODE = 14  # see AIDE's manual for details about exitcodes

    def __init__(self, server_config):
        self.server_config = server_config
        self.client_db_path = self._get_client_db_path(server_config.options.gen_img)
        self.aide_output_parser = AIDECheckParser(
                self.client_db_path, self.server_config.aide_reference_db_path)

    def generate_img(self):
        """Generate system image file for client whose AIDE configuration is
           identified by given unique client's ID (which is integer number) and
           return full path to the created system image."""

        system_img_path = None

        try:
            system_img_path = self._generate_img(self.client_db_path)
        except Exception as e:
            m = "Failed to generate system image based on the output of " \
                "comparison server's current configuration's state and "  \
                "client's '{}' AIDE database".format(self.client_db_path)
            raise SystemImageGeneratorError(m, e) from e

        system_img_path = os.path.realpath(system_img_path)

        logger.info("Successfully created system image '{}' for client "
                    "identified by AIDE's database '{}'.".format(
                        system_img_path, self.client_db_path))

        return system_img_path

    def _get_client_db_path(self, client_db_version):
        """Find and get AIDE database that client's configuration database
           version refers to."""

        logger.debug("Searching AIDE database corresponding to the client's "
                     "database version '{}'.".format(client_db_version))

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
           replacing 'database' variable with path to 'client_db_path' database
           to be able run AIDE --check to compare current state and given state
           that corresponds to client's system configuration."""

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
        """Generate system image based on the AIDE --check output."""

        aidediff_f.seek(0)

        try:
            entries = self.aide_output_parser.read_all_entries(aidediff_f)
        except AIDECheckParserError as e:
            m = "Error occurred while parsing AIDE --check output"
            raise SystemImageGeneratorError(m, e) from e

        return self._generate_img_from_aide_entries(entries)

    def _generate_img_from_aide_entries(self, entries):
        return "TODO"  # TODO TODO TODO
