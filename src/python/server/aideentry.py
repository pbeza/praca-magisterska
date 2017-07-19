# -*- coding: utf-8 -*-
import base64
import logging

from enum import Enum

from server.error import ServerError

logger = logging.getLogger(__name__)


class AIDEEntryError(ServerError):
    pass


class AIDEEntries:
    """Container for all the types of AIDE entries, ie. added, removed and
       changed files."""

    def __init__(self):
        self.added_entries = {}
        self.removed_entries = {}
        self.changed_entries = {}


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


class AIDEPropertiesError(ServerError):
    pass


class AIDEProperties:
    """Properties of files tracked by AIDE."""

    REQUIRED_PROPERTIES = {
            "name", "lname", "attr", "perm", "inode", "bcount", "uid", "gid",
            "size", "mtime", "ctime", "lcount", "md5", "crc32"
        }

    def __init__(self, properties):
        AIDEProperties.assert_required_properties_present_in_dict(properties)

        for prop_name, prop_val in properties.items():
            setattr(self, prop_name, prop_val)

        if self.lname == "0":                           # if not a symlink
            self.lname = None                           # full path
        self.attr = int(self.attr)                      # attributes
        self.perm = int(self.perm)                      # permissions
        self.inode = int(self.inode)                    # i-node
        self.bcount = int(self.bcount)                  # block count
        self.uid = int(self.uid)                        # user ID
        self.gid = int(self.gid)                        # group ID
        self.size = int(self.size)                      # file size in bytes
        self.mtime = int(base64.b64decode(self.mtime))  # modification time
        self.ctime = int(base64.b64decode(self.ctime))  # change time
        self.lcount = int(self.lcount)                  # number of hard links
        if self.md5 == "0":                             # if not a file
            self.md5 = None
        if self.crc32 == "0":                           # if not a file
            self.crc32 = None

        # Reverse of below is: base64.b64encode(bytes.fromhex(md5))
        self.md5_decoded = base64.b64decode(self.md5).hex() if self.md5 else 0

        # There are 2 versions of CRC-32 (AIDE uses 1st one)
        #   (1) http://hash.online-convert.com/crc32-generator
        #   (2) http://hash.online-convert.com/crc32b-generator
        self.crc32_decoded = base64.b64decode(self.crc32).hex() if self.crc32 else 0

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


class AIDESimpleEntry:
    """Representation of one line of the added, removed or changed file from
       AIDE --check output. Every line consists of informative string if AIDE's
       'summarize_changes' option is set (which is guaranteed by this
       application) and full file path of the file."""

    def __init__(self, aide_info_str, file_path):
        self.aide_info_str = aide_info_str  # AIDE's 'summarize_changes' info
        self.file_path = file_path


class AIDEEntry:
    """Representation of added, removed and changed AIDE entry. This is
       structured, extended version of AIDESimpleEntry."""

    AIDE_INFO_STR_PATTERN = "YlZbpugamcinCAXSE"
    AIDE_INFO_STR_LEN = len(AIDE_INFO_STR_PATTERN)
    COMMENT_CHAR = "#"
    NO_CHANGE_CHAR = "."
    ATTR_ADDED_CHAR = "+"
    ATTR_REMOVED_CHAR = "-"
    ATTR_IGNORED_CHAR = ":"
    ATTR_NOT_CHECKED_CHAR = " "

    def __init__(self, aide_properties, aide_info_str, entry_type):
        self.aide_properties = aide_properties
        self._assert_valid_aide_info_str(aide_info_str)
        self.aide_info_str = aide_info_str
        self.ftype = FileType(self.aide_info_str[0])
        self.entry_type = entry_type
        self.aide_prev_properties = None  # properties before change loaded elsewhere :(

    def _assert_valid_aide_info_str(self, aide_info_str):
        INVALID_SET = {"added", "removed", "changed"}

        if aide_info_str and aide_info_str.lower() in INVALID_SET:
            m = "Required 'summarize_changes' probably not set in AIDE "\
                "configuration file (invalid AIDE's info-string)"
            raise AIDEEntryError(m)

        if len(aide_info_str) != self.AIDE_INFO_STR_LEN:
            m = "Unexpected length of the AIDE changed properties info string"
            raise AIDEEntryError(m)

    def get_aide_changed_properties(self):
        # The general format of the AIDE info string is like the string
        # YlZbpugamcinCAXSE (see AIDE manual)

        p = self.aide_properties
        pp = self.aide_prev_properties
        properties = [
            ["name",           self.ftype.name if self.ftype else "?",         self.ftype.name if self.ftype else "?"],
            ["symlink",        p.lname if p.lname else "not symlink",          pp.lname if pp.lname else "?"],
            ["size",           self._get_size_change_info_str(),               "?"],
            ["block count",    p.bcount,                                       pp.bcount],
            ["permissions",    p.perm,                                         pp.perm],
            ["user id",        p.uid,                                          pp.uid],
            ["group id",       p.gid,                                          pp.gid],
            ["atime",          "",                                             ""],
            ["mtime",          p.mtime,                                        pp.mtime],
            ["ctime",          p.ctime,                                        pp.ctime],
            ["inode",          p.inode,                                        pp.inode],
            ["hardlinks",      p.lcount,                                       pp.lcount],
            ["md5 crc32",      "{} {}".format(p.md5_decoded, p.crc32_decoded), "{} {}".format(pp.md5_decoded, pp.crc32_decoded)],
            ["acl",            "",                                             ""],
            ["extended attrs", "",                                             ""],
            ["selinux attrs",  "",                                             ""],
            ["attrs 2nd part", "",                                             ""]
        ]
        aide_char_mapping = {
            self.NO_CHANGE_CHAR:        "no change",
            self.ATTR_IGNORED_CHAR:     "ignored",
            self.ATTR_NOT_CHECKED_CHAR: "not checked",
            self.ATTR_ADDED_CHAR:       "added",
            self.ATTR_REMOVED_CHAR:     "removed"
        }
        commented_out_properties = {
            self.NO_CHANGE_CHAR,
            self.ATTR_IGNORED_CHAR,
            self.ATTR_NOT_CHECKED_CHAR
        }
        s = ["# {}".format(p[1]) for p in properties[:3]]
        s.append("# {}".format(self.aide_info_str))

        for i in range(3, self.AIDE_INFO_STR_LEN):
            prop_name = properties[i][0]
            prop_val = properties[i][1]
            c = self.aide_info_str[i]

            if c == self.AIDE_INFO_STR_PATTERN[i]:
                line = "{:<45} # CHANGED from value '{}' ({})"
                # prev_prop_val = str(vars(self.aide_prev_properties))  # TODO TODO TODO
                prev_prop_val = properties[i][2]
                s.append(line.format(prop_val, prev_prop_val, prop_name))
            else:
                comment = aide_char_mapping.get(c)
                if not comment:
                    m = "Unrecognized AIDE character '{}'".format(c)
                    raise AIDEEntryError(m)
                prefix = "# " if c in commented_out_properties else ""
                line = "{:<45} # {} ({})".format(prefix + str(prop_val),
                                                 comment, prop_name)
                s.append(line)

        return s

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
