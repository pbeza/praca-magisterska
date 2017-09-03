# -*- coding: utf-8 -*-
import logging
import os
import progressbar
import shutil
import stat
import tarfile

import diff_match_patch as patcher

from myscm.client.error import ClientError
from myscm.client.sysimgmanager import SysImgManager
from myscm.client.sysimgvalidator import SysImgValidator
from myscm.client.sysimgvalidator import get_new_old_property_from_string
from myscm.client.sysimgvalidator import run_fun_for_each_report_line
from myscm.common.signaturemanager import SignatureManager
from myscm.server.aideentry import AIDEEntry
from myscm.server.aideentry import FileType
from myscm.server.sysimggenerator import SystemImageGenerator

progressbar.streams.wrap_stderr()
logger = logging.getLogger(__name__)


class SysImgExtractorError(ClientError):
    pass


class SysImgExtractor:

    def __init__(self, client_config):
        self.client_config = client_config
        self.sys_img_manager = SysImgManager(client_config)
        self.sys_img_validator = SysImgValidator(self.client_config.distro_name)

    def apply_sys_img(self):
        """Extract, validate and apply mySCM system image."""

        sys_img_path = self.sys_img_manager.get_sys_img_path()
        sys_img_ver = self.sys_img_manager.get_target_sys_img_ver_from_fname(
                                                                  sys_img_path)
        self.extracted_sys_img_dir = None

        try:
            with tarfile.open(sys_img_path) as sys_img_f:
                self.sys_img_validator.assert_sys_img_valid(sys_img_f)
                self.extracted_sys_img_dir = self._extract_sys_img(sys_img_f)

            logger.info("Applying changes from '{}' directory extracted from "
                        "'{}' mySCM system image.".format(
                            self.extracted_sys_img_dir, sys_img_path))

            self._apply_added_files(sys_img_f)
            self._apply_changed_files(sys_img_f)
            self._apply_removed_files(sys_img_f)
        except SysImgExtractorError:
            raise
        except Exception as e:
            m = "Failed to apply '{}' mySCM system image".format(
                    sys_img_f.name)
            raise SysImgExtractorError(m, e) from e

        self.sys_img_manager.update_current_system_state_version(sys_img_ver)
        self._remove_extracted_sys_img_dir()

        logger.info("Applying changes from '{}' mySCM system image ended "
                    "successfully.".format(sys_img_f.name))

    def _remove_extracted_sys_img_dir(self):
        logger.debug("Removing temporarily extracted system image '{}'."
                     .format(self.extracted_sys_img_dir))
        shutil.rmtree(self.extracted_sys_img_dir, ignore_errors=True)

    def _extract_sys_img(self, sys_img_f):
        sys_img_ext = SignatureManager.MYSCM_IMG_EXT
        extract_maindir = self.client_config.options.sys_img_extract_dir
        extract_subdir = sys_img_f.name.rstrip(sys_img_ext)
        extract_dir = os.path.join(extract_maindir, extract_subdir)

        logger.info("Extracting '{}' system image to temporary '{}' "
                    "directory...".format(sys_img_f.name, extract_dir))

        if os.path.exists(extract_dir):
            m = "Directory '{}' already exists - it may be caused if last "\
                "system upgrade has failed or was interrupred.".format(
                    extract_dir)

            if self.client_config.options.force_apply:
                m += " --force-apply flag detected - removing '{}' and "\
                    "extracting '{}'.".format(extract_dir, sys_img_f.name)
                logger.warning(m)
                shutil.rmtree(extract_dir)
            else:
                raise SysImgExtractorError(m)

        sys_img_f.extractall(path=extract_dir)

        logger.info("Extracting '{}' system image to temporary '{}' "
                    "directory ended successfully.".format(sys_img_f.name,
                                                           extract_dir))

        return extract_dir

    #####################
    # Apply added files #
    #####################

    def _apply_added_files(self, sys_img_f):

        src = os.path.join(self.extracted_sys_img_dir,
                           SystemImageGenerator.IN_ARCHIVE_ADDED_DIR_NAME)
        dst = "/"

        logger.info("Applying newly added files from '{}' directory..."
                    .format(src))

        self._movetree(src, dst)
        added_packages = self._get_packages_of_added_files(sys_img_f)
        n = len(added_packages)

        logger.info("Applying newly added files from '{}' directory ended "
                    "successfully (files from {} package{}).".format(
                        src, n, "s" if n != 1 else ""))
        logger.debug("Packages of the added files: '{}'".format(
                     "', '".join(added_packages)))

    def _get_packages_of_added_files(self, sys_img_f):
        added_report_path = os.path.join(
                                      self.extracted_sys_img_dir,
                                      SystemImageGenerator.ADDED_FILES_FNAME)

        n = self.sys_img_validator.added_entries
        bar = progressbar.ProgressBar(max_value=n)

        logger.debug("Collecting packages' names of {} added file{}.".format(
                        n, "s" if n != 1 else ""))

        pkg_set = set()

        with open(added_report_path) as f:
            expected_added_count = 2
            run_fun_for_each_report_line(
                f, sys_img_f, self._added_files_per_line_fun,
                expected_added_count, self.client_config.distro_name,
                False, bar, pkg_set)

        return pkg_set

    def _added_files_per_line_fun(self, values, sys_img_f, *args):
        bar = args[0]
        pkg_set = args[1]
        pkg_name = values[1]
        if pkg_name != "?":
            pkg_set.add(pkg_name)
        bar.update(bar.value + 1)

    def _movetree(self, src, dst):
        """Move recursively source directory to destination directory
           efectively merging two directory trees.

           There is a problem with universal function that is able to copy all
           types of files. See: https://stackoverflow.com/a/7420617/1321680
           Note that neither shutil.copytree nor distutils.dir_util.copy_tree
           is able to handle copying special files (e.g. named pipes)."""

        # Count all files first to introduce progress bar

        total_to_move = 0

        for _, dirs, files in os.walk(src, followlinks=False):
            total_to_move += len(dirs) + len(files)

        bar = progressbar.ProgressBar(max_value=total_to_move)

        # Move recursively all types of files including pipes, symlinks and
        # others possibly from one filesystem to the another (which can't be
        # handled using move() call).

        for src_dir, dirs, files in os.walk(src, followlinks=False):
            dst_dir = os.path.realpath(src_dir.replace(src, dst, 1))

            # Create directory with the same stats

            if not os.path.exists(dst_dir):
                logger.debug("Creating '{}'.".format(dst_dir))
                os.makedirs(dst_dir, exist_ok=True)
                fstat = os.stat(src_dir)
                shutil.chown(dst_dir, user=fstat.st_uid, group=fstat.st_gid)
                shutil.copystat(src_dir, dst_dir, follow_symlinks=False)

            # Move all symlinks to directories

            for dir_name in dirs:
                src_symdir = os.path.join(src_dir, dir_name)

                if os.path.islink(src_symdir):
                    move_symlink = True
                    dst_symdir = os.path.join(dst_dir, dir_name)

                    if os.path.islink(dst_symdir):
                        m = "Directory symlink '{}' already exists - "\
                            "overwriting.".format(dst_symdir)
                        logger.warning(m)
                    elif os.path.exists(dst_symdir):
                        move_symlink = False
                        m = "File '{}' already exists and is not symlink - "\
                            "skipping copying."
                        logger.warning(m)

                    if move_symlink:
                        shutil.move(src_symdir, dst_symdir)
                        m = "Moving symlink '{}' to '{}'.".format(src_symdir,
                                                                  dst_symdir)
                        logger.debug(m)

                bar.update(bar.value + 1)

            # Move all files (including special files)

            for fname in files:
                dst_file = os.path.join(dst_dir, fname)

                if os.path.exists(dst_file):
                    m = "File '{}' already exist - overwritting.".format(
                            dst_file)
                    logger.warning(m)

                src_file = os.path.join(src_dir, fname)

                # shutil.move() copies symlinks and fifos unless copy to
                # different filesystem

                shutil.move(src_file, dst_file, copy_function=self._mycopy2)
                m = "Moving '{}' to '{}'.".format(src_file, dst_file)
                logger.debug(m)

                bar.update(bar.value + 1)

        # Remove empty directories

        self._remove_empty_dirs(src)

        os.sync()

    def _remove_empty_dirs(self, src):
        logger.debug("Removing empty directories from '{}'.".format(src))

        for path, _, _ in os.walk(src, topdown=False, followlinks=False):
            try:
                os.removedirs(path)
            except:
                pass

    def _mycopy2(self, src, dst):
        try:
            shutil.copy2(src, dst)
        except shutil.SpecialFileError:
            # Special file copy from one filesystem to the another is not
            # handled by standard function. ;-( For now only named pipes (FIFO)
            # are handled.
            if self._isfifo(src):
                os.mkfifo(dst)
                shutil.copystat(src, dst)
            else:
                raise

    def _isfifo(self, path):
        file_stat = os.stat(path)
        return stat.S_ISFIFO(file_stat.st_mode)

    #######################
    # Apply changed files #
    #######################

    def _apply_changed_files(self, sys_img_f):
        changed_report_path = os.path.join(
                                      self.extracted_sys_img_dir,
                                      SystemImageGenerator.CHANGED_FILES_FNAME)

        logger.info("Applying changed files listed in '{}' report...".format(
                        changed_report_path))

        n = self.sys_img_validator.changed_entries
        bar = progressbar.ProgressBar(max_value=n)

        with open(changed_report_path) as f:
            run_fun_for_each_report_line(
                f, sys_img_f, self._changed_files_per_line_fun,
                AIDEEntry.PROPERTIES_COUNT, self.client_config.distro_name,
                False, bar)

        changed_dir = os.path.join(
            self.extracted_sys_img_dir,
            SystemImageGenerator.IN_ARCHIVE_CHANGED_DIR_NAME)

        self._remove_empty_dirs(changed_dir)

        logger.info("Applying changed files listed in '{}' report ended "
                    "successfully.".format(changed_report_path))

    def _changed_files_per_line_fun(self, values, sys_img_f, *args):
        path = values[0]
        ftype = values[4]
        size_was_changed = values[5] in {">", "<"}

        # Modify file's content if content was modified

        if ftype == FileType.REGULAR_FILE.value and size_was_changed:
            self._apply_changed_file(path)

        # Modify permissions to file if permissions were modified

        new_perm, old_perm = get_new_old_property_from_string(values[8], path)
        self._change_file_permissions(new_perm, old_perm, path)

        # Modify owner and group of the file (owner/group must already exist!)

        new_uid, old_uid = get_new_old_property_from_string(values[9], path)
        new_gid, old_gid = get_new_old_property_from_string(values[10], path)
        self._change_file_uid_gid(new_uid, old_uid, new_gid, old_gid, path)

        # TODO TODO TODO Run apt-get or pacman if file is part of the package

        # Update progressbar

        bar = args[0]
        bar.update(bar.value + 1)

    def _change_file_permissions(self, new_perm, old_perm, path):
        if old_perm != ".":  # If permissions should be changed
            new_hex_perm = int(new_perm, 8)
            m = "Changing permissions of the '{}' to {}.".format(
                    path, oct(new_hex_perm))
            logger.debug(m)
            os.chmod(path, new_hex_perm)  # follow_symlinks=False ?

    def _change_file_uid_gid(self, new_uid, old_uid, new_gid, old_gid, path):
        uid = new_uid if old_uid != "." else -1
        gid = new_gid if old_gid != "." else -1

        if uid is not None or gid is not None:
            if old_uid == ".":
                old_uid = new_uid

            if old_gid == ".":
                old_gid = new_gid

            try:
                m = "Changing UID, GID of the '{}' from {}, {} to {}, {}."\
                    .format(path, old_uid, old_gid, new_uid, new_gid)
                # shutil.chown(path, uid, gid) doesn't have follow_symlinks arg
                os.chown(path, int(uid), int(gid), follow_symlinks=False)
            except Exception as e:
                m = "Failed to change UID, GID of the '{}' from {}, {} to "\
                    "{}, {}. Details: '{}'.".format(
                        path, old_uid, old_gid, new_uid, new_gid, e)
                logger.error(m)

    def _apply_changed_file(self, path):
        orig_path = os.path.join(
            self.extracted_sys_img_dir,
            SystemImageGenerator.IN_ARCHIVE_CHANGED_DIR_NAME,
            path.lstrip("/"))
        diff_path = orig_path + SystemImageGenerator.PATCH_EXT

        if os.path.isfile(diff_path):
            self._apply_patch_for_file(path, diff_path)
            os.remove(diff_path)
        elif os.path.isfile(orig_path):
            self._move_changed_file(path, orig_path)
        else:
            m = "Neither '{}' nor '{}' was found for '{}' which is marked as "\
                "changed. It is acceptable if myscm-cli applied changes "\
                "during last run.".format(diff_path, orig_path, path)
            logger.warning(m)

    def _move_changed_file(self, src, dst):
        if not os.path.isfile(dst):
            m = "'{}' was expected to exist during applying changes but "\
                "doesn't exist.".format(dst)
            logger.warning(m)

        logger.debug("Moving '{}' to '{}'.".format(src, dst))

        shutil.move(src, dst, copy_function=self._mycopy2)  # overwrite file

    def _apply_patch_for_file(self, path, patch_path):
        logger.debug("Applying patch '{}' for '{}'.".format(patch_path, path))

        patch_text = None

        with open(patch_path) as f:
            patch_text = f.read()

        with open(path, "r+") as f:
            text_to_patch = f.read()
            p = patcher.diff_match_patch()
            patches = p.patch_fromText(patch_text)
            patched_text, _ = p.patch_apply(patches, text_to_patch)
            f.seek(0)
            f.write(patched_text)
            f.truncate()

    #######################
    # Apply removed files #
    #######################

    def _apply_removed_files(self, sys_img_f):
        removed_report_path = os.path.join(
                                      self.extracted_sys_img_dir,
                                      SystemImageGenerator.REMOVED_FILES_FNAME)

        logger.info("Removing removed files listed in '{}' report...".format(
                        removed_report_path))

        n = self.sys_img_validator.removed_entries
        bar = progressbar.ProgressBar(max_value=n)

        with open(removed_report_path) as f:
            expected_removed_count = 2
            run_fun_for_each_report_line(f, sys_img_f,
                                         self._removed_files_per_line_fun,
                                         expected_removed_count,
                                         self.client_config.distro_name,
                                         False, bar)

        logger.info("Removing removed files listed in '{}' report ended "
                    "successfully...".format(removed_report_path))

    def _removed_files_per_line_fun(self, values, sys_img_f, *args):
        path = values[0]
        pkg = values[1]

        pkg_msg = " from package '{}'.".format(pkg) if pkg != "?" else "."
        m = "Removing '{}'{}".format(path, pkg_msg)
        logger.debug(m)

        os.remove(path)

        bar = args[0]
        bar.update(bar.value + 1)

        # TODO TODO TODO run apt-get or pacman
