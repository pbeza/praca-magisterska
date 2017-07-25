# -*- coding: utf-8 -*-
import logging
import os
import re

from server.error import ServerError

logger = logging.getLogger(__name__)


class AIDEDatabasesManagerError(ServerError):
    pass


class AIDEDatabasesManager:
    """Manager of the AIDE aide.db[.X] databases directories (X is integer).
       This manager is not AIDE's database parser (see AIDECheckParser class).
       This class is responsible only for renaming AIDE's databases after
       myscm-srv --scan to keep old databases saved (they are needed to run
       myscm-srv with --gen-img option."""

    def __init__(self, server_config):
        self.server_config = server_config

    def replace_old_aide_db_with_new_one(self):
        """Replace old aide.db.current directory with new aide.db.new and
           rename old aide.db.current to aide.db.X directory (X is integer)."""

        if os.path.isdir(self.server_config.aide_reference_db_dir):
            num = self.get_current_aide_db_number()
            self._rename_aide_reference_db_file_to_old(num)
            self._rename_aide_reference_db_dir_to_old(num)
        else:
            logger.debug("AIDE reference database file doesn't exist yet - "
                         "skipping renaming procedure for old database. "
                         "Renaming only new database to set reference "
                         "database.")

        self._rename_aide_new_db_file_to_reference_file()
        self._rename_aide_new_db_dir_to_reference_dir()

    def _rename_aide_reference_db_file_to_old(self, num):
        """Rename recently created aide.db file to aide.db.X, where X is
           next unassigned integer."""

        a = self.server_config.aide_reference_db_path
        b = self._get_new_path_for_old_db_file(num)

        self._rename(a, b)

    def _get_new_path_for_old_db_file(self, num):
        """Return temporary new path for old AIDE database file."""

        tmp_aide_old_db_file_pattern = os.path.join(
            self.server_config.aide_reference_db_dir,
            self.server_config.aide_reference_db_fname + ".{}")

        return tmp_aide_old_db_file_pattern.format(num)

    def _rename_aide_reference_db_dir_to_old(self, num):
        """Rename recently created aide.db directory to aide.db.X, where X is
           next unassigned integer."""

        a = self.server_config.aide_reference_db_dir
        b = self._get_new_path_for_old_db_dir(num)

        self._rename(a, b)

    def _get_new_path_for_old_db_dir(self, num):
        """Return new path for old AIDE database directory."""

        return self.server_config.aide_old_db_subdir_pattern.format(num)

    def _rename_aide_new_db_file_to_reference_file(self):
        """Rename aide.db.new file to aide.db."""

        a = self.server_config.aide_out_db_path
        b = os.path.join(self.server_config.aide_out_db_dir,
                         self.server_config.aide_reference_db_fname)

        self._rename(a, b)

    def _rename_aide_new_db_dir_to_reference_dir(self):
        """Rename temporary directory aide.db.new with currently newest AIDE
           database to aide.db.current to set reference database for subsequent
           myscm-srv runs."""

        a = self.server_config.aide_out_db_dir
        b = self.server_config.aide_reference_db_dir

        self._rename(a, b)

    def _rename(self, from_path, to_path):
        m = "Renaming '{}' to '{}'.".format(from_path, to_path)
        logger.info(m)

        try:
            os.replace(from_path, to_path)
        except OSError as e:
            m = "Unable to rename '{}' to '{}'".format(from_path, to_path)
            raise AIDEDatabasesManagerError(m, e) from e

    def get_current_aide_db_number(self):
        """Return integer X which corresponds to aide.db.X directory that
           newest aide.db will be moved to after next myscm-srv --scan."""

        return self.get_last_aide_db_number() + 1

    def get_last_aide_db_number(self):
        """Return integer X which corresponds to aide.db.X with greatest X."""

        numbers = []
        regex_str = self.server_config.aide_old_db_fname_pattern.format(r"(\d+)")
        regex = re.compile(regex_str)
        old_db_dir = os.fsencode(self.server_config.aide_old_db_dir)

        for f in os.listdir(old_db_dir):
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                num = int(match.group(1))
                numbers.append(num)

        numbers.sort()
        self._report_missing_aide_db_files(numbers)

        return numbers[-1] if numbers else -1

    def print_all_aide_db_paths_sorted(self):
        """Print on stdout all found AIDE databases."""

        l = self._get_all_aide_db_paths()
        l.sort()
        dir_path = self.server_config.aide_old_db_dir

        for fname in l:
            full_path = os.path.join(dir_path, fname)
            full_path = os.path.realpath(full_path)
            print(full_path)

    def _get_all_aide_db_paths(self):
        """Return list of all found AIDE databases directories."""

        paths = []
        regex_str = self.server_config.aide_old_db_fname_pattern.format(r"(\d+)")
        regex = re.compile(regex_str)
        old_db_dir = os.fsencode(self.server_config.aide_old_db_dir)

        for f in os.listdir(old_db_dir):
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                paths.append(fname)

        return paths

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
