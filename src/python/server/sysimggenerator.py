# -*- coding: utf-8 -*-
import logging
import os
import re

from common.cmd import run_cmd
from common.error import MySCMError
from tempfile import TemporaryFile, NamedTemporaryFile

logger = logging.getLogger(__name__)


class SystemImageGeneratorError(MySCMError):
    pass


class SystemImageGenerator:

    def __init__(self, server_config):
        self.server_config = server_config

    def generate_img(self, client_db_version):
        """Generate system image file for client whose AIDE configuration is
           identified by given unique client's ID (which is integer number) and
           return full path to the created system image."""

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

        logger.debug("Found client's AIDE database file '{}'".format(client_db_path))

        # TODO
        # system_img_path = os.path.realpath(self._generate_img(client_db_path))
        system_img_path = "TODO"
        self._generate_img(client_db_path)

        logger.info("Successfully created system image '{}' for client "
                    "identified by AIDE's database '{}'.".format(
                        system_img_path, client_db_path))

        return system_img_path

    def _generate_img(self, client_db_path):
        """Generate system image file for the client."""

        logger.debug("Generating system image based on current server's "
                     "configuration and AIDE database file '{}' that "
                     "corresponds to client's system configuration".format(
                        client_db_path))

        system_img_path = None

        try:
            system_img_path = self.__generate_img(client_db_path)
        except Exception as e:
            m = "Failed to generate system image based on the result of " \
                "comparison server's current configuration's state and "  \
                "client's '{}' AIDE database".format(client_db_path)
            raise SystemImageGeneratorError(m, e) from e

        return system_img_path

    def __generate_img(self, client_db_path):
        """Generates system image based on AIDE's --check result ran on the
           AIDE's temporary configuration file."""

        system_img_path = None

        with NamedTemporaryFile(mode="r+", suffix=".aide.conf") as tmp_aideconf_f:
            self._copy_aide_config_to_tmp_replacing_db_path(client_db_path, tmp_aideconf_f)

            with TemporaryFile(mode="r+", suffix=".aide.diff") as aidediff_f:
                self._save_aide_check_result_to_tmp_file(aidediff_f, tmp_aideconf_f)
                system_img_path = self._generate_img_from_aide_check_result(aidediff_f)

        return system_img_path

    def _copy_aide_config_to_tmp_replacing_db_path(self, client_db_path, tmp_f):
            aide_conf_path = self.server_config.options.AIDE_config_path
            with open(aide_conf_path) as conf_f:
                regex_str = r"\s*database\s*=\s*.*\s*"
                regex = re.compile(regex_str)
                new_conf_line = "database = file:{}\n".format(client_db_path)
                db_matches = 0

                for line in conf_f:
                    match = regex.fullmatch(line)
                    if match:
                        tmp_f.write(new_conf_line)
                        db_matches += 1
                    else:
                        tmp_f.write(line)

            if db_matches != 1:
                m = "Expected exactly one line with assignment to "         \
                    "'database' variable in '{}' AIDE's configuration file "\
                    "({} found)".format(aide_conf_path, db_matches)
                raise SystemImageGeneratorError(m)

    def _save_aide_check_result_to_tmp_file(self, aidediff_f, tmp_aideconf_f):
        cmd = ["aide", "--check", "-c", tmp_aideconf_f.name]
        tmp_aideconf_f.seek(0)
        completed_proc = run_cmd(cmd, False, aidediff_f)

        if completed_proc.returncode > 13:  # error code - see AIDE manual
            m = "Exitcode {} for command '{}'".format(
                 completed_proc.returncode, " ".join(cmd))
            raise SystemImageGeneratorError(m)

    def _generate_img_from_aide_check_result(self, aidediff_f):
        logger.debug("Position: {}".format(aidediff_f.tell()))
        # aidediff_f.seek(0)
        for line in aidediff_f:
            logger.debug(line)
        return "TODO"
