# -*- coding: utf-8 -*-
import logging
import os
import shutil
import binaryornot.check

from myscm.common.cmd import long_run_cmd, run_check_cmd, CommandLineError
from myscm.server.aidedbmanager import AIDEDatabasesManager
from myscm.server.aidedbmanager import AIDEDatabasesManagerError
from myscm.server.error import ServerError

logger = logging.getLogger(__name__)


class ScannerError(ServerError):
    pass


class Scanner:
    """Wrapper of the AIDE scanner."""

    COPIED_FILES_DIRNAME = "COPIED"

    def __init__(self, server_config):
        self.server_config = server_config

    def scan(self):
        """Scan system software and configuration using AIDE's --init option
           creating new reference AIDE database and renaming old one."""

        if is_reference_aide_db_outdated(self.server_config):
            try:
                self._scan()
            except CommandLineError as e:
                m = "AIDE --init wrapper error while executing AIDE's command"
                raise ScannerError(m, e) from e
            except AIDEDatabasesManagerError as e:
                m = "AIDE --init wrapper error. AIDE's databases manager error"
                raise ScannerError(m, e) from e
        else:
            m = "Current reference AIDE database '{}' is up-to-date. No need "\
                "to create new database. Nothing to do. Exiting.".format(
                    self.server_config.aide_reference_db_path)
            logger.info(m)

    def _scan(self):
        """Scan system looking for changes, replace old aide.db with new one
           and move old aide.db to aide.db.X (X is incremented integer)."""

        aide_db_manager = AIDEDatabasesManager(self.server_config)
        self._create_tmp_out_dir_if_doesnt_exist()

        aide_config_path = self.server_config.options.AIDE_config_path
        cmd = ["aide", "--init", "-c", aide_config_path]

        try:
            long_run_cmd(cmd, True, suffix_msg="to create new {}".format(
                            self.server_config.aide_reference_db_fname))
        except CommandLineError as e:
            m = "Make sure that `database[_out|_new]` variables provided in "\
                "AIDE configuration '{}' are valid".format(aide_config_path)
            raise ScannerError(m, e) from e

        aide_db_manager.replace_old_aide_db_with_new_one()
        self._copy_selected_tracked_dirs()

        m = "New reference AIDE database '{}' setup successful. Run "\
            "--list-db option to list all available AIDE databases created "\
            "so far.".format(self.server_config.aide_reference_db_path)
        logger.info(m)

    def _copy_selected_tracked_dirs(self):
        try:
            dst_dir_path = self._create_copied_files_dir()
            self.__copy_selected_tracked_dirs_to_scan_dir(dst_dir_path)
        except OSError as e:
            m = "Failed to copy files that were specified in AIDE '{}' "\
                "configuration to be copied to myscm-srv --scan result".format(
                    self.server_config.options.AIDE_config_path)
            raise ScannerError(m, e) from e

    def _create_copied_files_dir(self):
        dst_dir_path = os.path.join(self.server_config.aide_reference_db_dir,
                                    self.COPIED_FILES_DIRNAME)
        os.makedirs(dst_dir_path)
        return dst_dir_path

    def __copy_selected_tracked_dirs_to_scan_dir(self, dst_dir_path):
        src_paths = self.server_config.get_all_realpaths_of_files_to_copy()
        n = len(src_paths)

        if n > 0:
            m = "Copying {} file{} and/or director{} selected in AIDE "\
                "configuration '{}' to '{}' directory. Please wait, it may "\
                "take some time to finish...".format(
                    n,
                    "s" if n > 1 else "",
                    "y" if n == 1 else "ies",
                    self.server_config.options.AIDE_config_path,
                    dst_dir_path)
            logger.info(m)
        else:
            m = "No files needs to be copied to '{}' directory. See '{}' "\
                "AIDE configuration file to investigate why.".format(
                    dst_dir_path, self.server_config.options.AIDE_config_path)
            logger.debug(m)

        # Sort paths to skip e.g. /x/y/z if /x/y was already copied.

        src_paths.sort()
        common_path = "/non-existing-path-to-initialize-loop"

        for src in src_paths:
            if os.path.commonpath([src, common_path]) == common_path:
                logger.debug("Skipping copying '{}' since it was copied while "
                             "copying '{}'.".format(src, common_path))
                continue

            common_path = src
            dst_file_path = os.path.join(dst_dir_path, src.lstrip(os.sep))
            os.makedirs(os.path.dirname(dst_file_path), exist_ok=True)

            if os.path.isdir(src):
                shutil.copytree(src, dst_file_path, ignore=self.ignore_handler)
                logger.debug("'{}' directory copied recursively successfully "
                             "to '{}' directory.".format(src, dst_file_path))
            elif check_if_copy_file(src):
                shutil.copy2(src, dst_file_path)
                logger.debug("'{}' file copied successfully.".format(
                             dst_file_path))

    def _create_tmp_out_dir_if_doesnt_exist(self):
        try:
            os.makedirs(self.server_config.aide_out_db_dir, exist_ok=True)
        except OSError as e:
            m = "Unable to create temporary directory '{}' for storing "\
                "result of the AIDE --init call"
            raise ScannerError(m, e) from e

    def check_if_copy_file(self, path):
        if_copy = None
        details = None
        is_dir = None

        try:
            if_copy = not binaryornot.check.is_binary(path)
            is_dir = os.path.isdir(path)
        except Exception as e:
            if_copy = False
            details = e

        m = "'{}' is not copied since it's non-text file".format(path)

        if details:
            m += ". Details: {}".format(details)

        if not if_copy and not is_dir:
            logger.debug(m)

        return if_copy

    def ignore_handler(self, dir_path, dir_content):
        return [f for f in dir_content if not self.check_if_copy_file(os.path.join(dir_path, f))]


def is_reference_aide_db_outdated(server_config):
    """Return True if reference AIDE database aide.db is outdated."""

    aide_config_path = server_config.options.AIDE_config_path
    completed_proc = run_check_cmd(aide_config_path, False)
    uptodate_msg = "AIDE found NO differences between database and "\
                   "filesystem. Looks okay!!"
    return uptodate_msg not in completed_proc.stdout.decode("utf-8")
