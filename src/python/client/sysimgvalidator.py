# -*- coding: utf-8 -*-
import hashlib
import logging
import os
import platform
import re
import stat

from client.error import ClientError
from server.aideentry import AIDEEntry
from server.aideentry import FileType
from server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SysImgValidatorError(ClientError):
    pass


class SysImgValidator:

    MD5SUM_LEN = 32
    SHA1SUM_LEN = 40

    def __init__(self, distro_name):
        self.distro_name = distro_name

    def assert_sys_img_valid(self, sys_img_f):
        try:
            self._assert_valid_sys_img(sys_img_f)
        except Exception as e:
            m = "Failed to validate '{}' system image".format(sys_img_f.name)
            raise SysImgValidatorError(m, e) from e

    def _assert_valid_sys_img(self, sys_img_f):
        logger.info("Checking whether myscm system image file '{}' is valid."
                    .format(sys_img_f.name))

        a1, a2 = self._assert_added_summary_valid(sys_img_f)
        c1, c2 = self._assert_changed_summary_valid(sys_img_f)
        r1, r2 = self._assert_removed_summary_valid(sys_img_f)

        m = "myscm system image file '{}' seems to be valid. {} added files "\
            "({} lines in report), {} changed files ({} lines in report), {} "\
            "removed files ({} lines in report).".format(
                sys_img_f.name, a2, a1, c2, c1, r2, r1)
        logger.info(m)

        # Variables needed for sysimgextractor's module progressbar

        self.added_entries = a2
        self.changed_entries = c2
        self.removed_entries = r2

    def _assert_added_summary_valid(self, sys_img_f):
        expected_added_count = 2
        return self._assert_summary_valid(
                                sys_img_f,
                                SystemImageGenerator.ADDED_FILES_FNAME,
                                expected_added_count,
                                self._assert_added_line_valid)

    def _assert_changed_summary_valid(self, sys_img_f):
        expected_changed_count = AIDEEntry.PROPERTIES_COUNT
        return self._assert_summary_valid(
                                sys_img_f,
                                SystemImageGenerator.CHANGED_FILES_FNAME,
                                expected_changed_count,
                                self._assert_changed_line_valid)

    def _assert_removed_summary_valid(self, sys_img_f):
        expected_removed_count = 2
        return self._assert_summary_valid(
                                sys_img_f,
                                SystemImageGenerator.REMOVED_FILES_FNAME,
                                expected_removed_count,
                                self._assert_removed_line_valid)

    def _assert_summary_valid(self, sys_img_f, path, val_count, fun):
        self._assert_file_present_in_sys_img(sys_img_f, path)
        return self._run_assert_fun_for_each_line(
                                path, sys_img_f, fun, val_count)

    def _assert_file_present_in_sys_img(self, sys_img_f, path):
        try:
            sys_img_f.getmember(path)
        except KeyError:
            m = "Missing '{}' file in '{}' myscm system image".format(
                    path, sys_img_f.name)
            raise SysImgValidatorError(m)

    def _run_assert_fun_for_each_line(self, path, sys_img_f, fun, n):
        all_lines = None
        valid_lines = None

        with sys_img_f.extractfile(path) as f:
            all_lines, valid_lines = run_fun_for_each_report_line(
                        f, sys_img_f, fun, n, self.distro_name)

        return all_lines, valid_lines

    ##############################################
    # Assert line from added.txt report is valid #
    ##############################################

    def _assert_added_line_valid(self, values, sys_img_f):
        added_file_path = values[0]

        self._assert_added_file_not_on_local_system(added_file_path, sys_img_f)
        self._assert_added_file_in_sys_img_added_files(added_file_path,
                                                       sys_img_f)

    def _assert_added_file_not_on_local_system(self, path, sys_img_f):
        """Make sure that file that is about to be added to the local
          filesystem doesn't exist on the local system yet."""

        if os.path.exists(path):
            m = "'{}' was about to be added during applying '{}' myscm-img "\
                "but it already exists in the local filesystem.".format(
                    path, sys_img_f.name)
            raise SysImgValidatorError(m)
        else:
            m = "'{}' reported in added.txt doesn't exist yet in the local "\
                "filesystem - it's OK since we want to add it to the system."\
                .format(path)
            logger.debug(m)

    def _assert_added_file_in_sys_img_added_files(self, path, myscm_img_f):
        intar_path = os.path.join(
              SystemImageGenerator.IN_ARCHIVE_ADDED_DIR_NAME, path.lstrip("/"))

        try:
            myscm_img_f.getmember(intar_path)
        except KeyError:
            m = "File '{}' is supposed to be present in myscm system image "\
                "'{}' in '{}' directory but was not found (info read from "\
                "added files report)".format(
                    intar_path, myscm_img_f.name,
                    SystemImageGenerator.IN_ARCHIVE_ADDED_DIR_NAME)
            raise SysImgValidatorError(m)
        else:
            m = "File '{}' found in '{}' in '{}' directory.".format(
                    path, myscm_img_f.name,
                    SystemImageGenerator.IN_ARCHIVE_ADDED_DIR_NAME)
            logger.debug(m)

    ################################################
    # Assert line from changed.txt report is valid #
    ################################################

    def _assert_changed_line_valid(self, values, sys_img_f):

        # Check whether changed file exists on local filesystem

        path = values[0]
        self._assert_changed_file_exists_on_local_filesystem(path, sys_img_f)

        # Get stat for file for further assertions

        file_stat = os.stat(path)

        # Check if file type is as declared in changed.txt report

        ftype_char = values[4]
        self._assert_changed_ftype_valid(path, ftype_char, file_stat)

        # Check if hash sums are as declared

        if ftype_char == FileType.REGULAR_FILE.value:
            md5sum_str = values[15]
            sha1sum_str = values[16]
            self._assert_file_checksums_valid(path, md5sum_str, sha1sum_str)

            # Check file size

            file_size_str = values[6]
            self._assert_changed_file_size_valid(path, file_size_str,
                                                 file_stat)

            # Check if changed file or its patch (diff) exists in myscm-img

            new_sha1sum, old_sha1sum = get_new_old_property_from_string(
                                                            sha1sum_str, path)
            file_content_changed = (old_sha1sum != new_sha1sum and
                                    old_sha1sum != ".")
            if file_content_changed:
                self._assert_changed_file_in_sys_img_changed_files(path,
                                                                   sys_img_f)

        # Check file permissions

        perm_str = values[8]
        self._assert_changed_perm_valid(path, perm_str, file_stat)

        # Check file UID

        uid_str = values[9]
        self._assert_changed_uid_valid(path, uid_str, file_stat)

        # Check file GID

        gid_str = values[10]
        self._assert_changed_gid_valid(path, gid_str, file_stat)

        # Check file mtime

        mtime_str = values[11]
        self._assert_changed_mtime_valid(path, mtime_str, file_stat)

        # Check file ctime

        ctime_str = values[12]
        self._assert_changed_ctime_valid(path, ctime_str, file_stat)

        # Check file link count

        lcount_str = values[14]
        self._assert_changed_lcount_valid(path, lcount_str, file_stat)

    def _assert_changed_file_exists_on_local_filesystem(self, path, sys_img_f):
        if not os.path.exists(path):
            m = "'{}' was about to be changed during applying '{}' myscm-img "\
                "but it doesn't exist in the local filesystem.".format(
                    path, sys_img_f.name)
            raise SysImgValidatorError(m)
        else:
            logger.debug("'{}' reported in changed.txt already exist - it's "
                         "OK since we want to change it.".format(path))

    def _assert_changed_file_in_sys_img_changed_files(self, path, sys_img_f):
        """Make sure that file that is about to be changed is present in the
           myscm system image (or its patch a.k.a. diff)."""

        intar_orig_path = os.path.join(
            SystemImageGenerator.IN_ARCHIVE_CHANGED_DIR_NAME,
            path.lstrip("/"))

        found_path = None

        try:
            sys_img_f.getmember(intar_orig_path)
            found_path = intar_orig_path
        except KeyError:
            intar_diff_path = intar_orig_path + SystemImageGenerator.PATCH_EXT
            try:
                sys_img_f.getmember(intar_diff_path)
                found_path = intar_diff_path
            except KeyError:
                m = "File '{}' or its patch '{}' is supposed to be present "\
                    "in myscm system image '{}' in '{}' directory but was "\
                    "not found (info read from added files report)".format(
                        intar_orig_path, intar_diff_path, sys_img_f.name,
                        SystemImageGenerator.IN_ARCHIVE_CHANGED_DIR_NAME)
                raise SysImgValidatorError(m)

        m = "File '{}' found in '{}' in '{}' directory.".format(
                found_path, sys_img_f.name,
                SystemImageGenerator.IN_ARCHIVE_CHANGED_DIR_NAME)
        logger.debug(m)

    def _assert_changed_ftype_valid(self, path, ftype_char, file_stat):
        validator_mapping = {
            FileType.REGULAR_FILE.value:
                os.path.isfile,
            FileType.DIRECTORY.value:
                os.path.isdir,
            FileType.SYMBOLIC_LINK.value:
                os.path.islink,
            FileType.CHARACTER_DEVICE.value:
                lambda _: stat.S_ISCHR(file_stat.st_mode),
            FileType.BLOCK_DEVICE.value:
                lambda _: stat.S_ISBLK(file_stat.st_mode),
            FileType.FIFO.value:
                lambda _: stat.S_ISFIFO(file_stat.st_mode),
            FileType.UNIX_SOCKET.value:
                lambda _: stat.S_ISSOCK(file_stat.st_mode),
            FileType.SOLARIS_DOOR.value:
                lambda _: stat.S_ISDOOR(file_stat.st_mode),
            FileType.SOLARIS_EVENT_PORT.value:
                lambda _: stat.S_ISPORT(file_stat.st_mode)
        }
        validator_fun = None

        try:
            validator_fun = validator_mapping[ftype_char]
        except KeyError:
            m = "Unknown file type of '{}' indentified by '{}' character "\
                "read from myscm system's image changed files report".format(
                    path, ftype_char)
            raise SysImgValidatorError(m)

        if not validator_fun(path):
            m = "File '{}' was declared in system's myscm image changed "\
                "files report as a '{}' but it isn't".format(
                    path, FileType(ftype_char).name)
            raise SysImgValidatorError(m)

    def _assert_file_checksums_valid(self, path, md5sum_str, sha1sum_str):
        self._assert_file_md5sum_valid(path, md5sum_str)
        self._assert_file_sha1sum_valid(path, sha1sum_str)

    def _assert_file_md5sum_valid(self, path, md5sum_str):
        self._assert_file_checksum_valid(path, "MD5", md5sum_str,
                                         self.MD5SUM_LEN,
                                         self._compute_file_md5sum)

    def _assert_file_sha1sum_valid(self, path, sha1sum_str):
        self._assert_file_checksum_valid(path, "SHA1", sha1sum_str,
                                         self.SHA1SUM_LEN,
                                         self._compute_file_sha1sum)

    def _assert_file_checksum_valid(self, path, hash_name, hash_str, hash_len,
                                    checksum_fun):
        expected_checksum = self._get_hash_from_property_string(hash_str, path,
                                                                hash_len)
        computed_checksum = checksum_fun(path)

        if computed_checksum != expected_checksum:
            m = "{} checksum of the '{}' file is '{}' instead of expected "\
                "'{}' (read from myscm system's image file)".format(
                    hash_name, path, computed_checksum, expected_checksum)
            raise SysImgValidatorError(m)

    def _get_hash_from_property_string(self, hash_str, path, checksum_len):
        checksum = self._get_expected_val_from_property_string(hash_str, path)

        if len(checksum) != checksum_len:
            m = "Hash string '{}' read from changed report for '{}' is "\
                "malformed".format(hash_str, path)
            raise SysImgValidatorError(m)

        return checksum

    def _get_expected_val_from_property_string(self, val_str, path):
        new_val, old_val = get_new_old_property_from_string(val_str, path)
        # '=' for size check, '.' for others
        return new_val if old_val in {".", "="} else old_val

    def _compute_file_md5sum(self, path):
        return self._compute_file_hash(path, hashlib.md5())

    def _compute_file_sha1sum(self, path):
        return self._compute_file_hash(path, hashlib.sha1())

    def _compute_file_hash(self, path, hash_type):
        hash_sum = None

        try:
            hash_sum = self.__get_file_hash(path, hash_type)
        except Exception as e:
            m = "Failed to compute hash of the '{}' file".format(path)
            raise SysImgValidatorError(m)

        return hash_sum

    def _assert_changed_file_size_valid(self, path, file_size_str, file_stat):
        local_file_size = file_stat.st_size
        expected_file_size = self._get_expected_val_from_property_string(
                                                           file_size_str, path)
        try:
            expected_file_size = int(expected_file_size)
        except ValueError:
            m = "Previous '{}' file size is not integer as it supposed to be "\
                "(has value: '{}')".format(path, expected_file_size)
            raise SysImgValidatorError(m)

        if local_file_size != expected_file_size:
            m = "File size of the '{}' file is '{}' instead of expected '{}' "\
                "(read from myscm system's image file)".format(
                    path, local_file_size, expected_file_size)
            raise SysImgValidatorError(m)

    def _assert_changed_perm_valid(self, path, perm_str, file_stat):
        local_perm = oct(file_stat.st_mode)[2:]
        expected_perm = self._get_expected_val_from_property_string(perm_str,
                                                                    path)
        if local_perm != expected_perm:
            m = "Permissions of the '{}' file are {} instead of {} as they "\
                "supposed to be (read from myscm system's image file)".format(
                    path, local_perm, expected_perm)
            raise SysImgValidatorError(m)

    def _assert_changed_uid_valid(self, path, uid_str, file_stat):
        local_file_uid = file_stat.st_uid
        self._assert_changed_int_valid(path, local_file_uid, uid_str, "UID")

    def _assert_changed_gid_valid(self, path, gid_str, file_stat):
        local_file_gid = file_stat.st_gid
        self._assert_changed_int_valid(path, local_file_gid, gid_str, "GID")

    def _assert_changed_mtime_valid(self, path, mtime_str, file_stat):
        local_mtime = int(file_stat.st_mtime)  # from float
        self._assert_changed_int_valid(path, local_mtime, mtime_str, "mtime",
                                       True)

    def _assert_changed_ctime_valid(self, path, ctime_str, file_stat):
        local_ctime = int(file_stat.st_ctime)  # from float
        self._assert_changed_int_valid(path, local_ctime, ctime_str, "ctime",
                                       True)

    def _assert_changed_lcount_valid(self, path, lcount_str, file_stat):
        local_lcount = file_stat.st_nlink
        self._assert_changed_int_valid(path, local_lcount, lcount_str,
                                       "lcount")

    def _assert_changed_int_valid(self, path, local_val, val_str, name,
                                  noexcept=False):
        expected_val = self._get_expected_val_from_property_string(val_str,
                                                                   path)
        try:
            expected_val = int(expected_val)
        except ValueError:
            m = "{} of the '{}' file is not integer as it supposed to be "\
                "(is: '{}')".format(name, path, expected_val)
            raise SysImgValidatorError(m)

        if local_val != expected_val:
            m = "{} of the '{}' file is '{}' instead of expected '{}' (read "\
                "from myscm system's image file)".format(name, path, local_val,
                                                         expected_val)
            if noexcept:
                logger.warning(m)
            else:
                raise SysImgValidatorError(m)

    def __get_file_hash(self, path, hash_type):
        BUF_SIZE = 65536  # read in 64kb chunks

        with open(path, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                hash_type.update(data)

        return hash_type.hexdigest()

    ################################################
    # Assert line from removed.txt report is valid #
    ################################################

    def _assert_removed_line_valid(self, values, sys_img_f):
        removed_file_path = values[0]

        if not os.path.exists(removed_file_path):
            m = "'{}' was about to be removed during applying '{}' myscm-img "\
                "but it doesn't exist on the local filesystem."\
                .format(removed_file_path, sys_img_f.name)
            logger.warning(m)  # raise SysImgValidatorError(m)
        else:
            logger.debug("'{}' reported in removed.txt exist it's OK since we "
                         "want to remove it from the system.".format(
                            removed_file_path))


def run_fun_for_each_report_line(report_f, sys_img_f, fun, n, distro_name,
                                 decode=True, *args):
    line_no = 0
    valid_lines = 0

    for l in report_f:
        line_no += 1
        line = l.decode("utf-8") if decode else l
        line = line.strip()

        if line.startswith("#"):
            _assert_valid_system_version(line, distro_name)
        elif line:
            valid_lines += 1
            values = [p.strip() for p in line.split("\0")]

            if len(values) != n:
                m = "Corrupted line '{}' in '{}' within '{}' (expected {} "\
                    "value{} in line, but {} found: {})".format(
                        line_no, report_f.name, sys_img_f.name, n,
                        "s" if n > 1 else "", len(values), line)
                raise SysImgValidatorError(m)

            fun(values, sys_img_f, *args)

    return line_no, valid_lines


def get_new_old_property_from_string(property_str, path):
    new_old_properties = property_str.split()

    if len(new_old_properties) != 2:
        m = "Property string '{}' for file '{}' is malformed".format(
                property_str, path)
        raise SysImgValidatorError(m)

    new_val = new_old_properties[0]
    old_val = new_old_properties[1].lstrip("(").rstrip(")")

    return new_val, old_val


def _assert_valid_system_version(comment, local_distro):
    expected_system = _get_system_from_comment(comment)
    expected_distro = _get_distro_from_comment(comment)
    expected_cpu_arch = _get_cpu_arch_from_comment(comment)
    name = None
    local = None
    expected = None
    msg = "Expected {} for given myscm system image is '{}' (local is '{}')"

    if expected_system:
        name = "system"
        local = platform.system()
        expected = expected_system
    elif expected_distro:
        name = "GNU/Linux distribution"
        local = local_distro
        expected = expected_distro
    elif expected_cpu_arch:
        name = "CPU architecture"
        local = platform.machine()
        expected = expected_cpu_arch

    if name and local.lower() != expected.lower():
        raise SysImgValidatorError(msg.format(name, expected, local))


def _get_system_from_comment(comment):
    return _get_value_from_comment(SystemImageGenerator.SYSTEM_STR, comment)


def _get_distro_from_comment(comment):
    return _get_value_from_comment(SystemImageGenerator.LINUX_DISTRO_STR,
                                   comment)


def _get_cpu_arch_from_comment(comment):
    return _get_value_from_comment(SystemImageGenerator.CPU_ARCHITECTURE_STR,
                                   comment)


def _get_value_from_comment(name, comment):
    regex_str = r"\s*#\s*{}\s*:\s*(.*)\s*".format(name)
    regex = re.compile(regex_str)
    match = regex.fullmatch(comment)
    return match.group(1) if match else None
