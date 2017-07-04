# -*- coding: utf-8 -*-
import logging
import os
import re

import common.config

logger = logging.getLogger(__name__)


class ServerConfigError(common.config.MySCMError):
    pass


class ServerConfig(common.config.BaseConfig):
    """Server-specific configuration manager."""

    def __init__(self, *options, **kwargs):
        super().__init__(*options, **kwargs)

        # AIDE 'database' related configuration option variables. 'database' is
        # path from which database is read.

        self.aide_reference_db_path = self._get_aide_reference_db_path()
        self.aide_reference_db_dir = os.path.dirname(self.aide_reference_db_path)
        self.aide_reference_db_fname = os.path.basename(self.aide_reference_db_path)

        # AIDE 'database_out' related configuration option related variables.
        # 'database_out' is path to which the new database is written to.

        self.aide_out_db_path = self._get_aide_out_db_path()
        self.aide_out_db_dir = os.path.dirname(self.aide_out_db_path)
        self.aide_out_db_fname = os.path.basename(self.aide_out_db_path)

        # Directory in which system images will be saved (TODO read from file conf)

        self.system_img_out_dir = "/tmp"

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
