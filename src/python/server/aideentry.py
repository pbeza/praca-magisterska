# -*- coding: utf-8 -*-
import base64
import logging

from enum import Enum

from server.error import ServerError

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
    CRC32 = "crc32"              # base64 encoded CRC32 (or 0 if eg. directory)


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
            PropertyType.CRC32: self._convert_to_hex_from_base64
        }

        for prop_name, prop_val in properties.items():
            prop_enum = None

            try:
                prop_enum = PropertyType(prop_name)
            except ValueError:
                self.extra_properties[prop_name] = prop_val
                self._save_encoded_in_extras_if_hash(prop_name, prop_val)
            else:
                prop_conv = properties_converter.get(prop_enum, int)
                self.properties[prop_enum] = prop_conv(prop_val)

    def _save_encoded_hash_in_extras(self, prop_name, prop_val):
        """AIDE encodes MD5 and CRC32. Save encoded hash for debugging."""

        if prop_name == PropertyType.MD5:
            self.extra_properties["md5encoded"] = prop_val
        elif prop_name == PropertyType.CRC32:
            self.extra_properties["crc32encoded"] = prop_val

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
            raise AIDEProperties(m)

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
        "C": [PropertyType.MD5, PropertyType.CRC32]
    }
    COMMENT_CHAR = "#"
    NO_CHANGE_CHAR = "."
    ATTR_ADDED_CHAR = "+"
    ATTR_REMOVED_CHAR = "-"
    ATTR_IGNORED_CHAR = ":"
    ATTR_NOT_CHECKED_CHAR = " "
    COMMENT_INDICATOR_CHARS = {
        NO_CHANGE_CHAR,
        ATTR_IGNORED_CHAR,
        ATTR_NOT_CHECKED_CHAR
    }
    AIDE_CHAR_TO_COMMENT_MAPPING = {
        NO_CHANGE_CHAR:        "no change",
        ATTR_IGNORED_CHAR:     "ignored",
        ATTR_NOT_CHECKED_CHAR: "not checked",
        ATTR_ADDED_CHAR:       "added",
        ATTR_REMOVED_CHAR:     "removed"
    }

    def __init__(self, aide_properties, aide_info_str, entry_type):
        self.aide_properties = aide_properties
        self._assert_valid_aide_info_str(aide_info_str)
        self.aide_info_str = aide_info_str
        self.ftype = FileType(self.aide_info_str[0])
        self.entry_type = entry_type
        self.aide_prev_properties = None  # TODO properties before change loaded elsewhere :(

    def _assert_valid_aide_info_str(self, aide_info_str):
        if len(aide_info_str) != self.AIDE_INFO_STR_FULL_LEN:
            m = "Unexpected length of the AIDE changed properties info string"
            raise AIDEEntryError(m)

    def get_aide_changed_properties(self):
        # The general format of the AIDE info string is like the string
        # YlZbpugamcinCAXSE (see AIDE manual).

        s = [
            self.aide_properties[PropertyType.NAME],
            self.ftype.name,
            self._get_size_change_info_str(),
            "# AIDE info  str: '{}'".format(self.aide_info_str)
        ]

        for i in range(3, self.AIDE_INFO_SUBSTR_LEN):
            cur_c = self.aide_info_str[i]
            ref_c = self.AIDE_INFO_STR_PATTERN[i]
            self._append_property_based_on_current_info_char(cur_c, ref_c, s)

        return s

    def _append_property_based_on_current_info_char(self, cur_c, ref_c, s):
        prop_types = self.AIDE_INFO_STR_TO_PROP_TYPES_MAPPING.get(ref_c)

        if prop_types is None:
            # Ignore additional, unnecessary AIDE properties
            return

        prop_names = [t.value for t in prop_types]
        # str() below is needed to convert None to 'None'
        prop_vals = [str(self.aide_properties[t]) for t in prop_types]
        prev_prop_vals = [str(self.aide_prev_properties[t]) for t in prop_types]

        prop_names_str = ", ".join(prop_names)
        prop_vals_str = " ".join(map(str, prop_vals))
        prev_prop_vals_str = " ".join(map(str, prev_prop_vals))

        line = None

        if cur_c == ref_c:  # if something has changed
            line = "{:<45} # CHANGED from {} ({})".format(
                        prop_vals_str, prev_prop_vals_str, prop_names_str)
        else:
            comment = self.AIDE_CHAR_TO_COMMENT_MAPPING.get(cur_c)
            if not comment:
                m = "Unrecognized AIDE infostring character '{}'".format(cur_c)
                raise AIDEEntryError(m)
            prefix = "# " if cur_c in self.COMMENT_INDICATOR_CHARS else ""
            prefix += prop_vals_str
            line = "{:<45} # {} ({})".format(prefix, comment, prop_names_str)

        s.append(line)

    def _get_size_change_info_str(self):
        info = "unrecognized size status"
        c = self.aide_info_str[2]

        if c == "=":
            info = "size has not changed"
        elif c == "<":
            info = "shrinked size"
        elif c == ">":
            info = "grown size"

        return info
