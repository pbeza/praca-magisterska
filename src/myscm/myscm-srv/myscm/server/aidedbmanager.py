# -*- coding: utf-8 -*-
import logging
import os
import re

from myscm.server.error import ServerError

logger = logging.getLogger(__name__)


class AIDEDatabasesManagerError(ServerError):
    pass


class AIDEDatabasesManager:
    """Manager of the AIDE aide.db[.X] databases directories (X is integer).

       This manager is not AIDE's database parser (see AIDECheckParser class).
       This class is responsible only for renaming AIDE's databases after
       myscm-srv --scan to keep old databases saved (they are needed to run
       myscm-srv with --gen-img option)."""

    def __init__(self, server_config):
        self.server_config = server_config

    def replace_old_aide_db_with_new_one(self):
        """Replace old aide.db.current directory with new aide.db.new and
           rename old aide.db.current to aide.db.X directory (X is integer)."""

        if os.path.isdir(self.server_config.aide_reference_db_dir):
            num = self.get_recent_aide_db_version()
            self._rename_aide_reference_db_file_to_old(num)
            self._rename_aide_reference_db_dir_to_old(num)
        else:
            logger.debug("AIDE reference database file doesn't exist yet - "
                         "skipping renaming procedure for old database. "
                         "Renaming only new database to set reference "
                         "database.")

        self._rename_aide_new_db_file_to_reference_file()
        self._rename_aide_new_db_dir_to_reference_dir()
        self.server_config.db_ver_file.increment()

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
        logger.debug(m)

        try:
            os.replace(from_path, to_path)
        except OSError as e:
            m = "Unable to rename '{}' to '{}'".format(from_path, to_path)
            raise AIDEDatabasesManagerError(m, e) from e

    def get_recent_aide_db_version(self):
        """Return integer X which corresponds to aide.db.X directory that
           newest aide.db will be moved to after next myscm-srv --scan."""

        # Get recent AIDE database version from file that holds it

        db_ver_file = self.server_config.db_ver_file
        db_ver_from_file = None

        try:
            db_ver_from_file = db_ver_file.get_version(create=False)
        except Exception as e:
            logger.warning("Parsing file '{}' has failed.".format(
                            db_ver_file.path))
            db_ver_from_file = -1

        # Get recent AIDE database reading directory with databases

        versions = self._get_aide_db_ver_list().sort()
        self._report_missing_aide_db_files(versions)
        db_ver_from_dir = versions[-1] if versions else -1

        # Compare both results to detect inconsistency

        if db_ver_from_file < db_ver_from_dir:
            m = "Recently generated AIDE database version read from '{}' is "\
                "{}, but there was found database file with version number {}"\
                .format(db_ver_file.path, db_ver_from_file, db_ver_from_dir)
            raise AIDEDatabasesManagerError(m)

        return db_ver_from_file

    def _get_aide_db_ver_list(self):
        versions = []
        regex_str = self.server_config.aide_old_db_fname_pattern.format(r"(\d+)")
        regex = re.compile(regex_str)
        old_db_dir = os.fsencode(self.server_config.aide_old_db_dir)

        for f in os.listdir(old_db_dir):
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                num = int(match.group(1))
                versions.append(num)

        return versions

    def print_all_aide_db_paths_sorted(self):
        """Print on stdout all found AIDE databases created with myscm-srv
           --scan option."""

        l = self._get_all_aide_db_paths()
        n = len(l)
        l.sort()
        dir_path = self.server_config.aide_old_db_dir

        if l:
            print("{} director{} created with myscm-srv --scan option:\n"
                  .format(n, "y" if n == 1 else "ies"))
        else:
            print("No directories created as a result of myscm-srv --scan "
                  "were found.")

        for fname in l:
            full_path = os.path.join(dir_path, fname)
            full_path = os.path.realpath(full_path)
            line = "    {}".format(full_path)
            print(line)

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

        if os.path.isdir(self.server_config.aide_reference_db_dir):
            paths.append(self.server_config.aide_reference_db_dir)

        return paths

    def _get_missing_aide_db_files_ranges(self, numbers):
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

        return ranges

    def _report_missing_aide_db_files(self, numbers):
        """Report to logger all of the old, missing AIDE databases aide.db.X.
           Removed old databases are not a problem as long as there is no need
           to generate system image from client's state that corresponds to the
           missing AIDE database."""

        ranges = self._get_missing_aide_db_files_ranges(numbers)

        if ranges:
            m = "Missing {}.X file{}, where X is: {}. This is not a "\
                "problem as long as client don't need to update its "\
                "configuration from this state.".format(
                  self.server_config.aide_reference_db_path,
                  "s" if len(ranges) > 1 else "",
                  ", ".join(ranges))
            logger.warning(m)
