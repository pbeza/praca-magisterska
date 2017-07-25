# -*- coding: utf-8 -*-
import logging
import os
import platform
import re

import common.config

from server.error import ServerError

logger = logging.getLogger(__name__)


class ServerConfigError(ServerError):
    pass


class ServerConfig(common.config.BaseConfig):
    """Server-specific configuration manager."""

    SUPPORTED_LINUX_DISTROS = {"debian", "arch"}

    def __init__(self, *options, **kwargs):
        super().__init__(*options, **kwargs)

        self.distro_name = self._assert_allowed_linux_distro()

        ###
        # AIDE 'database' related configuration option variables. 'database' is
        # path from which database is read.
        ###

        # '/var/myscm-srv/aide.db.current/aide.db' by default
        self.aide_reference_db_path = self._get_aide_reference_db_path()

        # '/var/myscm-srv/aide.db.current' by default
        self.aide_reference_db_dir = os.path.dirname(
                                                   self.aide_reference_db_path)

        # 'aide.db' by default
        self.aide_reference_db_fname = os.path.basename(
                                                   self.aide_reference_db_path)

        ###
        # AIDE 'database_out' related configuration option related variables.
        # 'database_out' is path to which the new database is written to.
        ###

        # '/var/myscm-srv/aide.db.new/aide.db.new' by default
        self.aide_out_db_path = self._get_aide_out_db_path()

        # '/var/myscm-srv/aide.db.new' by default
        self.aide_out_db_dir = os.path.dirname(self.aide_out_db_path)

        # 'aide.db.new' by default
        self.aide_out_db_fname = os.path.basename(self.aide_out_db_path)

        ###
        # Variables related to old AIDE databases paths.
        ###

        # '/var/myscm-srv/' by default
        self.aide_old_db_dir = os.path.dirname(self.aide_reference_db_dir)

        # '/var/myscm-srv/aide.db' by default
        self.aide_old_db_subdir_base = os.path.join(
                            self.aide_old_db_dir, self.aide_reference_db_fname)

        # 'aide.db.{}' by default (placeholder for integer)
        self.aide_old_db_fname_pattern = self.aide_reference_db_fname + ".{}"

        # '/var/myscm-srv/aide.db.{}' by default (placeholder for integer)
        self.aide_old_db_subdir_pattern = os.path.join(
                            self.aide_old_db_dir,
                            self.aide_old_db_fname_pattern)

        # '/var/myscm-srv/aide.db.{}/aide.db.{}' by default (placeholder for
        # integer)
        self.aide_old_db_path_pattern = os.path.join(
                            self.aide_old_db_subdir_pattern,
                            self.aide_old_db_fname_pattern)

    def _assert_allowed_linux_distro(self):
        os_name = platform.system()
        if not os_name:
            os_name = "unknown"

        if os_name.lower() != "linux":
            m = "This software runs on GNU/Linux operating system only ('{}' "\
                "was detected).".format(os_name)
            raise ServerConfigError(m)

        suffix_msg = "Only Arch and Debian distributions are supported."

        try:
            import distro
        except ImportError:
            m = "Can't check if GNU/Linux is supported! " + suffix_msg
            logger.warning(m)
        else:
            distro_name = distro.id()

            if distro_name not in self.SUPPORTED_LINUX_DISTROS:
                if not distro_name:
                    distro_name = "unknown"
                else:
                    distro_name = "'{}'".format(distro_name)

                logger.warning("Unsupported {} GNU/Linux distribution was "
                               "detected. {}".format(distro_name, suffix_msg))

        return distro_name

    def _get_aide_reference_db_path(self):
        """Return value of 'database' variable from AIDE configuration."""

        path = self._get_aide_value_for_key("database")
        return os.path.realpath(path)

    def _get_aide_out_db_path(self):
        """Return value of 'database_out' variable from AIDE configuration."""

        path = self._get_aide_value_for_key("database_out")
        return os.path.realpath(path)

    def _get_aide_value_for_key(self, key):
        """Return value for given key from AIDE configuration file."""

        value = None
        err = None

        try:
            value = self.__get_value_for_key(key)
        except Exception as e:
            err = e

        if value is None or err is not None:
            m = "AIDE configuration file '{}' probably doesn't have " \
                "'{}' variable assigned".format(self.options.AIDE_config_path,
                                                key)
            raise ServerConfigError(m, err)

        return value

    def __get_value_for_key(self, key):
        """Return value for given key from AIDE configuration file using
           regular expression."""

        value = None
        regex_str = r"\s*{}\s*=\s*(?:file:)?(.*)\s*".format(key)
        regex = re.compile(regex_str)

        with open(self.options.AIDE_config_path) as f:
            for line in f:
                match = regex.fullmatch(line)
                if match:
                    value = match.group(1)
                    break

        return value
