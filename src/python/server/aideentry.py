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
        self.added_entries = []
        self.removed_entries = []
        self.changed_entries = []


class FileType(Enum):
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

    REQUIRED_PROPERTIES = {
            "name", "lname", "attr", "perm", "inode", "bcount", "uid", "gid",
            "size", "mtime", "ctime", "lcount", "md5", "crc32"
        }

    def __init__(self, properties):
        AIDEProperties.assert_required_properties_present_in_dict(properties)

        self.aide_info_str = None  # AIDE's 'summarize_changes' info string
        self.ftype = None          # valid only if summarize_changes option set

        for prop_name, prop_val in properties.items():
            setattr(self, prop_name, prop_val)

        self._convert_from_str_to_types()

    def _convert_from_str_to_types(self):
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
        if self.md5:
            self.md5_decoded = base64.b64decode(self.md5).hex()

        # There are 2 versions of CRC-32 (AIDE uses 1st one - namely CRC-32B)
        #   (1) http://hash.online-convert.com/crc32-generator
        #   (2) http://hash.online-convert.com/crc32b-generator
        if self.crc32:
            self.crc32_decoded = base64.b64decode(self.crc32).hex()

        if self.aide_info_str:
            if self.aide_info_str.lower() in {"added", "removed", "changed"}:
                m = "Required 'summarize_changes' not set in AIDE "\
                    "configuration file"
                raise AIDEPropertiesError(m)
            else:
                ftype_char = self.aide_info_str[0]
                self.ftype = FileType(ftype_char)

    @staticmethod
    def assert_required_properties_present_in_dict(properties_dict):
        properties_set = {p for p in properties_dict}
        AIDEProperties.assert_required_properties_present(properties_set)

    @staticmethod
    def assert_required_properties_present(properties_set):
        A = AIDEProperties.REQUIRED_PROPERTIES
        B = set(properties_set)

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
        self.aide_info_str = aide_info_str
        self.file_path = file_path


#class AIDEEntry:
#    """Base class for added, moved, removed and removed AIDE entries."""
#
#    def __init__(self, aide_info_str, path):
#        self.aide_info_str = aide_info_str
#        self.path = path
#        self.file_type = self._aide_info_str_to_file_type(aide_info_str)
#
#    def _aide_info_str_to_file_type(self, aide_info_str):
#        ftype_char = aide_info_str[0]
#        ftype = None
#
#        try:
#            ftype = FileType(ftype_char)
#        except ValueError:
#            m = "Unexpected file type reported by AIDE (unexpected '{}' "\
#                "character in '{}' string)".format(ftype_char, aide_info_str)
#            raise AIDEParserError(m)
#
#        return ftype
#
#
#class AIDEAddedEntry(AIDEEntry):
#
#    def __init__(self, aide_info_str, path):
#        super().__init__(aide_info_str, path)
#        self.path = path
#
#
#class AIDERemovedEntry:
#
#    def __init__(self, path):
#        self.path = path
#
#
#class AIDEChangedEntry:
#
#    def __init__(self, path, gid, uid):
#        self.path = path
#        self.gid = gid
#        self.uid = uid
