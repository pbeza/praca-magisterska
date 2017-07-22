# -*- coding: utf-8 -*-
import logging
import re

from server.aidedbparser import AIDEDatabaseFileParser
from server.aideentry import AIDEEntries, AIDESimpleEntry, EntryType, AIDEProperties
from server.error import ServerError

logger = logging.getLogger(__name__)


class AIDECheckParserError(ServerError):
    pass


class AIDECheckParser:
    """Parser of the AIDE --check output. It's primary role is to generate
       structured information which files were added, removed and changed."""

    AIDE_SEPARATOR = "{}\n".format(51 * "-")
    ADDED_ENTRIES = "Added entries:\n"
    REMOVED_ENTRIES = "Removed entries:\n"
    CHANGED_ENTRIES = "Changed entries:\n"
    FILES_ATTRS = "The attributes of the (uncompressed) database(s):\n"
    DETAILED_INFO = "Detailed information about changes:\n"

    def __init__(self, client_aide_db_path, server_aide_db_path):
        self.aide_srv_db_parser = AIDEDatabaseFileParser(server_aide_db_path)
        self.aide_cli_db_parser = AIDEDatabaseFileParser(client_aide_db_path)

    def read_all_entries(self, aidediff_f):
        """Read added, removed and changed entries from AIDE --check output."""

        entries = None

        try:
            entries = self._read_all_entries(aidediff_f)
        except StopIteration:
            m = "Unexpected end of AIDE --check output while parsing it"
            raise AIDECheckParserError(m)

        return entries

    def _read_all_entries(self, aidediff_f):
        entries = self._set_added_removed_changed_entries(aidediff_f)
        self._set_entries_info_from_aide_db_file(entries)
        self._set_changed_properties_prev_values(entries.changed_entries)

        return entries

    def _set_added_removed_changed_entries(self, aidediff_f):
        entries = AIDEEntries()
        expected_entries_mapping = {
                self.ADDED_ENTRIES: self._set_added_entries,
                self.REMOVED_ENTRIES: self._set_removed_entries,
                self.CHANGED_ENTRIES: self._set_changed_entries
            }

        for i in range(len(expected_entries_mapping)):
            if not _read_to_line(aidediff_f, self.AIDE_SEPARATOR):
                m = "Expected 1st separator line not found in AIDE --check "\
                    "output"
                raise AIDECheckParserError(m)

            line = next(aidediff_f)
            read_entries_fun = expected_entries_mapping.get(line)

            if read_entries_fun:
                _read_assert_next_lines(aidediff_f, self.AIDE_SEPARATOR)
                read_entries_fun(aidediff_f, entries)
                del expected_entries_mapping[line]
            elif line in {self.FILES_ATTRS, self.DETAILED_INFO}:
                missing = [e.strip() for e in expected_entries_mapping.keys()]
                m = "{} sections ('{}') not found in --check AIDE output "\
                    "(this message is not an error nor warning).".format(
                        len(expected_entries_mapping), "', '".join(missing))
                logger.debug(m)
                break
            else:
                m = "Unexpected line '{}' after separator line in AIDE "\
                     "--check output".format(line.strip())
                raise AIDECheckParserError(m)

        return entries

    def _set_added_entries(self, aidediff_f, entries):
        entries.added_entries = self._create_simple_entries_from_lines_up_to_new_line(aidediff_f)

    def _set_removed_entries(self, aidediff_f, entries):
        entries.removed_entries = self._create_simple_entries_from_lines_up_to_new_line(aidediff_f)

    def _set_changed_entries(self, aidediff_f, entries):
        entries.changed_entries = self._create_simple_entries_from_lines_up_to_new_line(aidediff_f)

    def _set_entries_info_from_aide_db_file(self, entries):
        """Replace AIDESimpleEntry entries with AIDEEntry entries by fetching
           more information about AIDESimpleEntry entries from AIDE aide.db[.X]
           database file.

           Reading intermediate AIDESimpleEntry entries first and later
           replacing them by AIDEEntry entries is needed to avoid rereading
           aide.db[.X] database N times where N is number of all entries."""

        entries.added_entries = self.aide_srv_db_parser.get_files_entries(
                                EntryType.ADDED, entries.added_entries)
        entries.removed_entries = self.aide_cli_db_parser.get_files_entries(
                                EntryType.REMOVED, entries.removed_entries)
        entries.changed_entries = self.aide_srv_db_parser.get_files_entries(
                                EntryType.CHANGED, entries.changed_entries)

        logger.info("{} files added, {} removed, {} changes since client's "
                    "declared last update.".format(
                                len(entries.added_entries),
                                len(entries.removed_entries),
                                len(entries.changed_entries)))

    def _set_changed_properties_prev_values(self, changed_entries):
        # TODO this method shouldn't be here

        s = set(changed_entries.keys())
        old_properties = self.aide_cli_db_parser.get_files_properties(s)

        for k, v in old_properties.items():
            e = changed_entries.get(k)

            if not e:
                m = "Can't find previous properties for changed file '{}'"\
                    .format(k)
                raise AIDECheckParserError(m)

            changed_entries[k].aide_prev_properties = AIDEProperties(v)

    def _create_simple_entries_from_lines_up_to_new_line(self, aidediff_f):
        d = {}

        # Ignore leading empty lines

        for line in aidediff_f:
            if line != "\n":
                file_entry = self._get_simple_aide_entry(line)
                d[file_entry.file_path] = file_entry
                break

        # Read until empty line

        for line in aidediff_f:
            if line != "\n":
                file_entry = self._get_simple_aide_entry(line)
                d[file_entry.file_path] = file_entry
            else:
                break

        return d

    def _get_simple_aide_entry(self, line):
        """Get AIDE summarize string and file path."""

        regex_str = r"\s*(.*):\s*(.*)\s*"
        regex = re.compile(regex_str)
        match = regex.fullmatch(line)

        if not match or len(match.groups()) != 2:
            m = "AIDE output file entry unexpected format '{}'".format(line)
            raise AIDECheckParserError(m)

        file_info = match.group(1)
        file_path = match.group(2)

        return AIDESimpleEntry(file_info, file_path)


def _read_to_line(aidediff_f, searched_line):
    """Read given file until given line is found."""

    read_lines = 0
    was_found = False

    for line in aidediff_f:
        read_lines += 1
        if line == searched_line:
            was_found = True
            break

    return read_lines if was_found else 0


def _read_assert_next_lines(aidediff_f, *expected_lines):
    """Read given file until series of all expected lines are read or any
       of the expected lines differs from actual file's content."""

    read_lines = 0

    for expected_line in expected_lines:
        read_lines += 1
        line = next(aidediff_f)
        if line != expected_line:
            m = "Unexpected line '{}'. '{}' line was expected".format(
                    line.strip(), expected_line.strip())
            raise AIDECheckParserError(m)

    return read_lines
