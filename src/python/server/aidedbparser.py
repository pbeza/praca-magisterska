# -*- coding: utf-8 -*-
import logging
import urllib.parse

from server.aideentry import AIDEProperties
from server.error import ServerError

logger = logging.getLogger(__name__)


class AIDEDatabaseFileParserError(ServerError):
    pass


class AIDEDatabaseFileParser:
    """Parser of the aide.db[.X] AIDE databases (X is integer)."""

    AIDE_DB_FILE_OPENING = "@@begin_db\n"
    AIDE_DB_FILE_CLOSING = "@@end_db\n"
    AIDE_DB_PROPERTIES_OPENING = "@@db_spec"
    AIDE_INFO_STR = "aide_info_str"

    def __init__(self, aide_db_path):
        """Constructor initialized by full file path of the parsed AIDE
           aide.db[.X] database file created with AIDE's --init option."""

        self.aide_db_path = aide_db_path

    def get_files_entries(self, aide_simple_entries):
        requested_paths = {e.file_path for e in aide_simple_entries}
        files_properties = self.get_files_properties(requested_paths)
        for e in aide_simple_entries:
            files_properties[e.file_path][self.AIDE_INFO_STR] = e.aide_info_str
        return {AIDEProperties(v) for _, v in files_properties.items()}

    def get_files_properties(self, requested_paths, requested_properties=None):
        """Wrapper handling errors for the the actual _get_files_properties()
           function."""

        if not requested_properties:
            requested_properties = AIDEProperties.REQUIRED_PROPERTIES
        elif isinstance(requested_properties, str):
            requested_properties = {requested_properties}

        if not isinstance(requested_properties, set) or\
           not isinstance(requested_paths, set):
            m = "get_files_properties() got unexpected parameters"
            raise AIDEDatabaseFileParserError(m)

        files_properties = {}
        try:
            files_properties = self._get_files_properties(requested_paths,
                                                          requested_properties)
        except OSError as e:
            m = "Failed to get files' AIDE properties. Unable to open AIDE "\
                "database file '{}'".format(self.aide_db_path)
            raise AIDEDatabaseFileParserError(m, e) from e

        return files_properties

    def _get_files_properties(self, requested_paths, requested_properties):
        """Return dictionary of dictionaries where key of the outer dictionary
           is requested file's full path and value is another dictionary with
           AIDE requested properties of the file fetched from AIDE database."""

        files_properties = {}

        if not requested_paths:
            return files_properties

        # File needs to be open with "b" flag to be able to seek relative to
        # file's end. See: https://stackoverflow.com/a/21533561/1321680

        with open(self.aide_db_path) as db_file:
            infile_prop_names = self._get_all_infile_properties_names(db_file)
            self._assert_required_properties_present(infile_prop_names)
            self._assert_requested_properties_present(requested_properties,
                                                      infile_prop_names)
            prop_col_mapping = self._enumerate_columns(infile_prop_names)
            files_properties = self._get_files_properties_values(
                                    requested_paths, requested_properties,
                                    prop_col_mapping, db_file)

        return files_properties

    def _enumerate_columns(self, infile_prop_names):
        prop_cols_dict = {}
        column_no = 0

        for prop_name in infile_prop_names:
            prop_cols_dict[prop_name] = column_no
            column_no += 1

        return prop_cols_dict

    def _get_all_infile_properties_names(self, db_file):
        line = next(db_file)
        self._assert_expected_opening(line)
        searched_word = self.AIDE_DB_PROPERTIES_OPENING
        words = []

        for line in db_file:
            words = line.split(maxsplit=1)
            if words and words[0] == searched_word:
                words = words[1].split()
                break

        if not words:
            m = "Malformed AIDE database, '{}' not found".format(searched_word)
            raise AIDEDatabaseFileParserError(m)

        return words

    def _get_files_properties_values(self, requested_paths,
                                     requested_properties,
                                     prop_col_mapping,
                                     db_file):
        files_properties = {}
        N = len(prop_col_mapping)
        line = None

        for line in db_file:
            words = line.split(maxsplit=1)
            self._assert_not_empty_properties_values_list(words)
            path = urllib.parse.unquote(words[0])  # unquote full path

            if path not in requested_paths:
                continue

            words = line.split()
            n = len(words)
            self._assert_expected_number_of_properties_values(n, N)
            words[0] = urllib.parse.unquote(words[0])  # unquote full path
            current_file_properties = {}

            for prop_name in requested_properties:
                prop_col = prop_col_mapping[prop_name]
                current_file_properties[prop_name] = words[prop_col]

            files_properties[path] = current_file_properties

        self._assert_expected_closing(line)

        return files_properties

    def _assert_expected_opening(self, line):
        if line != self.AIDE_DB_FILE_OPENING:
            m = "AIDE database file '{}' is probably malformed since it "\
                "doesn't have '{}' valid opening".format(
                        self.aide_db_path, self.AIDE_DB_FILE_OPENING)
            raise AIDEDatabaseFileParserError(m)

    def _assert_expected_closing(self, line):
        if line != self.AIDE_DB_FILE_CLOSING:
            m = "AIDE database file '{}' is probably malformed since it "\
                "doesn't have '{}' valid closing".format(
                        self.aide_db_path, self.AIDE_DB_FILE_CLOSING)
            raise AIDEDatabaseFileParserError(m)

    def _assert_expected_number_of_properties_values(self, n, N):
        if n != N:
            m = "Malformed '{}' AIDE database file - unexpected number "\
                "of properties ({} instead of {})".format(
                        self.aide_db_path, n, N)
            raise AIDEDatabaseFileParserError(m)

    def _assert_not_empty_properties_values_list(self, values):
            if not values:
                m = "Malformed '{}' AIDE database - unexpected empty line "\
                    "instead of line with file's properties values".format(
                        self.aide_db_path)
                raise AIDEDatabaseFileParserError(m)

    def _assert_required_properties_present(self, infile_prop_names):
        AIDEProperties.assert_required_properties_present(infile_prop_names)

    def _assert_requested_properties_present(self, requested_properties,
                                             infile_prop_names):
        A = requested_properties
        B = set(infile_prop_names)

        if not A.issubset(B):
            A_str = "', '".join(A)
            B_str = "', '".join(B)
            m = "Some of the requested file's AIDE properties were not found "\
                "- list of requested properties: '{}'; list of fetched "\
                "properties: '{}'".format(A_str, B_str)
            raise AIDEDatabaseFileParserError(m)
