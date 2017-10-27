# -*- coding: utf-8 -*-
import base64
import logging

from enum import Enum

from myscm.server.error import ServerError
import myscm.server.pkgmanager as pkgmgr

logger = logging.getLogger(__name__)


class EntryType(Enum):
    """All types of AIDE entries."""

    ADDED = 1
    REMOVED = 2
    CHANGED = 3


class FileType(Enum):
    """All types of files supported by AIDE."""

    REGULAR_FILE = "f"
    DIRECTORY = "d"
    SYMBOLIC_LINK = "l"
    CHARACTER_DEVICE = "c"
    BLOCK_DEVICE = "b"
    FIFO = "p"
    UNIX_SOCKET = "s"
    SOLARIS_DOOR = "D"
    SOLARIS_EVENT_PORT = "P"
    FTYPE_CHANGED = "!"
    UNKNOWN = "?"


class AIDEEntries:
    """Container for all the types of AIDE entries, ie. added, removed and
       changed one."""

    def __init__(self):
        self.added_entries = {}
        self.removed_entries = {}
        self.changed_entries = {}


class PropertyType(Enum):
    """Selected, required types of properties supported by AIDE."""

    NAME = "name"                # file name
    LNAME = "lname"              # link name
    ATTR = "attr"                # attributes
    PERM = "perm"                # permissions
    INODE = "inode"              # i-node
    BCOUNT = "bcount"            # block count
    UID = "uid"                  # user ID
    GID = "gid"                  # group ID
    SIZE = "size"                # file size in bytes
    MTIME = "mtime"              # modification time
    CTIME = "ctime"              # change time
    LCOUNT = "lcount"            # number of hard links
    MD5 = "md5"                  # base64 encoded MD5 (or 0 if eg. directory)
    SHA1 = "sha1"                # base64 encoded SHA1 (or 0 if eg. directory)


class AIDEPropertiesError(ServerError):
    pass


class AIDEProperties:
    """Properties of files tracked by AIDE."""

    REQUIRED_PROPERTIES = {p.value for p in PropertyType}

    def __init__(self, properties):
        AIDEProperties.assert_required_properties_present_in_dict(properties)

        self.properties = {}        # required properties only
        self.extra_properties = {}  # not required properties only
        properties_converter = {    # not listed properties are integers
            PropertyType.NAME: str,
            PropertyType.LNAME: self._convert_to_none_if_zero,
            PropertyType.MTIME: self._convert_to_int_from_base64,
            PropertyType.CTIME: self._convert_to_int_from_base64,
            PropertyType.MD5: self._convert_to_hex_from_base64,
            PropertyType.SHA1: self._convert_to_hex_from_base64,
        }

        for prop_name, prop_val in properties.items():
            prop_enum = None

            try:
                prop_enum = PropertyType(prop_name)
            except ValueError:
                self.extra_properties[prop_name] = prop_val
            else:
                prop_conv = properties_converter.get(prop_enum, int)
                self.properties[prop_enum] = prop_conv(prop_val)
                self._save_encoded_in_extras_if_hash(prop_enum, prop_val)

    def _save_encoded_in_extras_if_hash(self, prop_enum, prop_val):
        """AIDE encodes hashes (eg. MD5). Save encoded hash for debugging."""

        hashes_set = {PropertyType.MD5, PropertyType.SHA1}

        if prop_enum in hashes_set:
            key = "{}encoded".format(prop_enum.value)
            self.extra_properties[key] = prop_val

    def _convert_to_hex_from_base64(self, val):
        # Reverse of below is: base64.b64encode(bytes.fromhex(md5))
        # There are 2 versions of CRC-32 (AIDE uses 1st one)
        #   (1) http://hash.online-convert.com/crc32-generator
        #   (2) http://hash.online-convert.com/crc32b-generator
        return base64.b64decode(val).hex() if val != "0" else None

    def _convert_to_none_if_zero(self, val):
        return val if val != "0" else None

    def _convert_to_int_from_base64(self, val):
        return int(base64.b64decode(val))

    @staticmethod
    def assert_required_properties_present_in_dict(properties_dict):
        properties_set = set(properties_dict.keys())
        AIDEProperties.assert_required_properties_present(properties_set)

    @staticmethod
    def assert_required_properties_present(properties_set):
        A = AIDEProperties.REQUIRED_PROPERTIES
        B = properties_set

        if not A.issubset(B):
            A_str = "', '".join(A)
            B_str = "', '".join(B)
            m = "Some of the required file's AIDE properties were not found "\
                "- list of fetched properties: '{}', list of required "\
                "properties: '{}'".format(B_str, A_str)
            raise AIDEPropertiesError(m)

    def __getitem__(self, key):
        val = None

        try:
            val = self.properties[key]
        except KeyError:
            val = self.extra_properties[key]

        return val


class AIDESimpleEntry:
    """Representation of one line of the added, removed or changed file from
       AIDE --check output. Every line consists of informative string if AIDE's
       'summarize_changes' option is set (which is guaranteed by this
       application) and full file path of the file."""

    def __init__(self, aide_info_str, file_path):
        self.aide_info_str = aide_info_str  # AIDE's 'summarize_changes' info
        self.file_path = file_path


class PropertyHeader:

    def __init__(self, name, formatter="{:<25}"):
        self.name = name
        self.formatter = formatter

    def get_name(self):
        return self.formatter.format(self.name)


class AIDEEntryError(ServerError):
    pass


class AIDEEntry:
    """Representation of added, removed and changed AIDE entry. This is
       structured, extended version of `AIDESimpleEntry`."""

    AIDE_INFO_STR_PATTERN = "YlZbpugamcinCAXSE"
    AIDE_INFO_STR_FULL_LEN = len(AIDE_INFO_STR_PATTERN)
    AIDE_INFO_SUBSTR_LEN = AIDE_INFO_STR_FULL_LEN - 4  # ignore last 4 chars
    AIDE_INFO_STR_TO_PROP_TYPES_MAPPING = {
        "l": [PropertyType.NAME],
        "b": [PropertyType.BCOUNT],
        "p": [PropertyType.PERM],
        "u": [PropertyType.UID],
        "g": [PropertyType.GID],
        "m": [PropertyType.MTIME],
        "c": [PropertyType.CTIME],
        "i": [PropertyType.INODE],
        "n": [PropertyType.LCOUNT],
        "C": [PropertyType.MD5, PropertyType.SHA1]
    }
    COMMENT_CHAR = "#"
    NO_CHANGE_CHAR = "."
    ATTR_ADDED_CHAR = "+"
    ATTR_REMOVED_CHAR = "-"
    ATTR_IGNORED_CHAR = ":"
    ATTR_NOT_CHECKED_CHAR = " "
    AIDE_ALLOWED_INFO_STR_CHARS = {
        NO_CHANGE_CHAR,
        ATTR_IGNORED_CHAR,
        ATTR_NOT_CHECKED_CHAR,
        ATTR_ADDED_CHAR,
        ATTR_REMOVED_CHAR
    }
    CHANGED_FILES_HEADER_NAMES = [
        PropertyHeader("# " + PropertyType.NAME.value, "{:<50}"),
        PropertyHeader(PropertyType.LNAME.value, "{:<50}"),
        PropertyHeader("aide_info_str", "{:<24} "),
        PropertyHeader("attr", "{:<18}"),
        PropertyHeader("ftype", "{:<10}"),
        PropertyHeader("size_change", "{:<16}"),
        PropertyHeader("size"),
        PropertyHeader(PropertyType.BCOUNT.value),
        PropertyHeader(PropertyType.PERM.value),
        PropertyHeader(PropertyType.UID.value),
        PropertyHeader(PropertyType.GID.value),
        PropertyHeader(PropertyType.MTIME.value, "{:<30}"),
        PropertyHeader(PropertyType.CTIME.value, "{:<30}"),
        PropertyHeader(PropertyType.INODE.value),
        PropertyHeader(PropertyType.LCOUNT.value, "{:<12}"),
        PropertyHeader(PropertyType.MD5.value, "{:<73}"),
        PropertyHeader(PropertyType.SHA1.value, "{:<100}"),
        PropertyHeader("package")
    ]
    PROPERTIES_COUNT = len(CHANGED_FILES_HEADER_NAMES)

    def __init__(self, aide_properties, aide_info_str, entry_type):
        self.aide_properties = aide_properties
        self._assert_valid_aide_info_str(aide_info_str)
        self.aide_info_str = aide_info_str
        self.ftype = FileType(self.aide_info_str[0])
        self.entry_type = entry_type
        # properties before change (loaded elsewhere)
        self.aide_prev_properties = None

    def get_full_path(self):
        return self.aide_properties[PropertyType.NAME]

    def was_file_content_changed(self):
        return self.aide_info_str[12] == 'C'

    def _assert_valid_aide_info_str(self, aide_info_str):
        if len(aide_info_str) != self.AIDE_INFO_STR_FULL_LEN:
            m = "Unexpected length of the AIDE changed properties info string"
            raise AIDEEntryError(m)

    def get_aide_changed_properties(self, server_config):
        # The general format of the AIDE info string is like the string
        # YlZbpugamcinCAXSE (see AIDE manual).

        cur_size = self.aide_properties[PropertyType.SIZE]
        prev_size = self.aide_prev_properties[PropertyType.SIZE]

        s = [
            self.aide_properties[PropertyType.NAME],
            str(self.aide_properties[PropertyType.LNAME]),  # str() for None
            self.aide_info_str,
            str(self.aide_properties[PropertyType.ATTR]),  # https://unix.stackexchange.com/a/343020/28115
            self.ftype.value,
            self.aide_info_str[2],
            "{} ({})".format(cur_size,
                             "=" if cur_size == prev_size else prev_size)
        ]

        comment_entry = True

        for i in range(3, self.AIDE_INFO_SUBSTR_LEN):
            cur_c = self.aide_info_str[i]
            ref_c = self.AIDE_INFO_STR_PATTERN[i]
            entry_changed = self._append_property_based_on_current_info_char(
                                                               cur_c, ref_c, s)
            if comment_entry and entry_changed:
                comment_entry = False

        fpath = self.aide_properties[PropertyType.NAME]
        pkg_name = pkgmgr.get_file_package_name(fpath, server_config)
        s.append(pkg_name)

        if comment_entry:
            s[0] = "# {}".format(s[0])

        return s

    def _append_property_based_on_current_info_char(self, cur_c, ref_c, s):
        prop_types = self.AIDE_INFO_STR_TO_PROP_TYPES_MAPPING.get(ref_c)

        if prop_types is None:
            # Ignore additional, unnecessary properties defined in AIDE config
            return

        entry_changed = False

        if cur_c == ref_c:
            entry_changed = True
        elif cur_c not in self.AIDE_ALLOWED_INFO_STR_CHARS:
            m = "Unrecognized AIDE info string character '{}'".format(cur_c)
            raise AIDEEntryError(m)

        # str() below is needed to convert None to 'None'
        prop_vals = [str(self.aide_properties[t]) for t in prop_types]
        prev_prop_vals = [str(self.aide_prev_properties[t]) for t in prop_types]

        for i in range(len(prop_vals)):
            if not entry_changed and prop_vals[i] != prev_prop_vals[i]:
                m = "Current and previous value for property '{}' are not "\
                    "equal despite AIDE reported they are not different"\
                    .format(ref_c)
                raise AIDEEntryError(m)

            prop_val_str = str(prop_vals[i])
            prev_prop_val_str = str(prev_prop_vals[i]) if entry_changed else cur_c
            line = "{} ({})".format(prop_val_str, prev_prop_val_str)
            s.append(line)

        return entry_changed
