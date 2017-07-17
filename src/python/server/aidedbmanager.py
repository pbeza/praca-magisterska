# -*- coding: utf-8 -*-

import logging
import os
import re

from server.error import ServerError

logger = logging.getLogger(__name__)


class AIDEDatabasesManagerError(ServerError):
    pass


class AIDEDatabasesManager:
    """Manager of the AIDE aide.db[.X] databases (X is integer). This manager
       is not AIDE's database parser - it only renames AIDE's databases if
       requested to do so."""

    def __init__(self, server_config):
        self.server_config = server_config

    def replace_old_aide_db_with_new_one(self):
        """Replace old aide.db with new aide.db.new and rename old aide.db."""

        if os.path.isfile(self.server_config.aide_reference_db_path):
            self._rename_aide_reference_db_to_old_fname()
        else:
            logger.debug("AIDE reference database file doesn't exist yet - "
                         "skipping renaming procedure for old database.")
        self._rename_aide_new_db_to_reference_fname()

    def _rename_aide_reference_db_to_old_fname(self):
        """Rename recently created aide.db to aide.db.X, where X is next
           unassigned integer."""

        a = self.server_config.aide_reference_db_path
        b = self._get_new_fpath_for_old_db()
        logger.debug("Renaming old database '{}' to '{}'.".format(a, b))

        try:
            os.rename(a, b)
        except OSError as e:
            m = "Unable to rename old database '{}' to '{}'".format(a, b)
            raise AIDEDatabasesManagerError(m, e) from e

    def _rename_aide_new_db_to_reference_fname(self):
        """Rename newly created database aide.db.new to aide.db to set
           reference database for AIDE subsequent runs."""

        a = self.server_config.aide_out_db_path
        b = self.server_config.aide_reference_db_path
        logger.info("Renaming new database '{}' to '{}'.".format(a, b))

        try:
            os.rename(a, b)
        except OSError as e:
            m = "Unable to rename new database '{}' to '{}'".format(a, b)
            raise AIDEDatabasesManagerError(m, e) from e

    def _get_new_fpath_for_old_db(self):
        """Return new path for old AIDE database."""

        num = self.get_last_aide_db_number()
        fname = "{}.{}".format(self.server_config.aide_reference_db_fname,
                               num + 1)
        return os.path.join(self.server_config.aide_reference_db_dir, fname)

    def get_current_aide_db_number(self):
        """Return integer X which corresponds to aide.db.X that aide.db will
           have after next --scan."""
        return self.get_last_aide_db_number() + 1

    def get_last_aide_db_number(self):
        """Return integer X which corresponds to aide.db.X with greatest X."""

        regex_str = r"{}.(\d+)".format(
                                    self.server_config.aide_reference_db_fname)
        regex = re.compile(regex_str)
        aide_dir = os.fsencode(self.server_config.aide_reference_db_dir)
        numbers = []

        for f in os.listdir(aide_dir):
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                num = int(match.group(1))
                numbers.append(num)

        numbers.sort()
        self._report_missing_aide_db_files(numbers)

        return numbers[-1] if numbers else -1

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
                ranges.append("0")
            else:
                ranges.append("0-{}".format(numbers[0] - 1))

        for i in range(len(numbers) - 1):
            a, b = numbers[i], numbers[i + 1]
            if a + 1 < b:
                if b - a == 2:
                    ranges.append(str(a + 1))
                else:
                    ranges.append("{}-{}".format(a + 1, b - 1))

        if ranges:
            m = "Missing {}.X file{}, where X is: {}. This is not a "\
                "problem as long as client don't need to update its "\
                "configuration from this state.".format(
                  self.server_config.aide_reference_db_path,
                  "s" if len(ranges) > 1 else "",
                  ", ".join(ranges))
            logger.warning(m)
