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

        # AIDE 'database' config option related variables
        self.aide_reference_db_path = self._get_aide_reference_db_path()
        self.aude_reference_db_dir = os.path.dirname(self.aide_reference_db_path)
        self.aude_reference_db_fname = os.path.basename(self.aide_reference_db_path)

        # AIDE 'database_new' config option related variables
        self.aide_new_db_path = self._get_aide_new_db_path()
        self.aide_new_db_dir = os.path.dirname(self.aide_new_db_path)
        self.aide_new_db_fname = os.path.basename(self.aide_new_db_path)

    def set_new_aide_reference_db(self):
        if os.path.isfile(self.aide_reference_db_path):
            self._rename_aide_reference_db_to_old_fname()
        else:
            logger.debug("AIDE reference database file doesn't exist yet - "
                         "skipping renaming procedure")
        self._rename_aide_new_db_to_reference_fname()

    def _rename_aide_new_db_to_reference_fname(self):
        """Rename newly created database aide.db.new to aide.db to set
           reference database for AIDE subsequent runs."""
        a = self.aide_new_db_path
        b = self.aide_reference_db_path
        logger.info("Renaming new database '{}' to '{}'".format(a, b))

        try:
            os.rename(a, b)
        except OSError as e:
            msg = "Unable to rename new database '{}' to '{}'".format(a, b)
            raise ServerConfigError(msg, e) from e

    def _rename_aide_reference_db_to_old_fname(self):
        """Rename recently created aide.db to aide.db.X, where X is next
           unassigned integer."""
        a = self.aide_reference_db_path
        b = self._get_new_fpath_for_old_db()
        logger.info("Renaming old database '{}' to '{}'".format(a, b))

        try:
            os.rename(a, b)
        except OSError as e:
            msg = "Unable to rename old database '{}' to '{}'".format(a, b)
            raise ServerConfigError(msg, e) from e

    def _get_new_fpath_for_old_db(self):
        """Return new path for old AIDE database."""
        num = self._get_last_conf_number()
        fname = '{}.{}'.format(self.aide_reference_db_path, num + 1)
        return os.path.join(self.aude_reference_db_dir, fname)

    def _get_last_conf_number(self):
        """Return integer X which corresponds to aide.db.X with greatest X."""
        regex_str = r'{}.(\d+)'.format(self.aude_reference_db_fname)
        regex = re.compile(regex_str)
        aide_dir = os.fsencode(self.aude_reference_db_dir)
        numbers = []

        for f in os.listdir(aide_dir):
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                num = int(match.group(1))
                numbers.append(num)

        numbers.sort()
        self._report_missing_aide_db_files(numbers)

        return numbers[-1] if numbers else 0

    def _report_missing_aide_db_files(self, numbers):
        """Report to logger all of the old, missing AIDE databases aide.db.X.
           Removed old databases are not a problem as long as there is no need
           to generate system image from client's state that corresponds to the
           missing AIDE database."""
        if not numbers:
            return

        ranges = []

        if numbers[0] > 0:
            if numbers[0] == 1:
                ranges.append('0')
            else:
                ranges.append('0-{}'.format(numbers[0] - 1))

        for i in range(len(numbers) - 1):
            a, b = numbers[i], numbers[i + 1]
            if a + 1 < b:
                if b - a == 2:
                    ranges.append(str(a + 1))
                else:
                    ranges.append('{}-{}'.format(a + 1, b - 1))

        if ranges:
            logger.warning('Missing {} file{}, where X is: {}'.format(
                            self.aide_reference_db_path,
                            's' if len(ranges) > 0 else '',
                            ', '.join(ranges)))

    def _get_aide_reference_db_path(self):
        """Return value of 'database' variable from AIDE configuration."""
        return self._get_aide_value_for_key('database')

    def _get_aide_new_db_path(self):
        """Return value of 'database_new' variable from AIDE configuration."""
        return self._get_aide_value_for_key('database_new')

    def _get_aide_value_for_key(self, key):
        """Return value for given key from AIDE configuration file."""
        value = None
        err = None

        try:
            value = self.__get_value_for_key(key)
        except Exception as e:
            err = e

        if value is None or err is not None:
            msg = "AIDE configuration file '{}' probably doesn't have "\
                  "'{}' variable assigned".format(
                                       self.options.AIDE_config_file_path, key)
            raise ServerConfigError(msg, err)

        return value

    def __get_value_for_key(self, key):
        """Return value for given key from AIDE configuration file using
           regular expression."""
        value = None
        regex_str = r'\s*({})\s*=\s*(?:file:)?(.*)\s*'.format(key)
        regex = re.compile(regex_str)

        with open(self.options.AIDE_config_file_path) as f:
            for line in f:
                match = regex.fullmatch(line)
                if match:
                    value = match.group(2)
                    break

        return value
