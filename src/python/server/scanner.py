# -*- coding: utf-8 -*-
import logging
import subprocess

from common.error import MySCMError
from server.aidedbmanager import AIDEDatabasesManager
from server.aidedbmanager import AIDEDatabasesManagerError
from server.config import ServerConfigError

logger = logging.getLogger(__name__)


class ScannerError(MySCMError):
    pass


class Scanner:

    def __init__(self, server_config):
        self.server_config = server_config
        self.aide_db_manager = AIDEDatabasesManager(self.server_config)

    def scan(self):
        """Scans system software and configuration using AIDE's --init
           option creating new reference AIDE database and renaming old one."""
        if self._is_reference_aide_db_outdated():
            try:
                self._scan()
            except ServerConfigError as e:
                raise ScannerError("Server configuration error", e) from e
            except AIDEDatabasesManagerError as e:
                raise ScannerError("AIDE databases manager error", e) from e
        else:
            msg = "Current reference AIDE database '{}' is up-to-date. No "\
                  "need to create new database. I have nothing to do - "\
                  "exiting.".format(self.server_config.aide_reference_db_path)
            logger.info(msg)

    def _is_reference_aide_db_outdated(self):
        cmd = [
            "aide", "--check", "-c",
            self.server_config.options.AIDE_config_file_path
        ]
        completed_proc = self._run_cmd(cmd, False)
        uptodate_msg = "AIDE found NO differences between database and filesystem. Looks okay!!"
        return uptodate_msg not in completed_proc.stdout.decode("utf-8")

    def _scan(self):
        cmd = [
            "aide", "--init", "-c",
            self.server_config.options.AIDE_config_file_path
        ]
        completed_proc = self._run_cmd(cmd)
        self.aide_db_manager.replace_old_aide_db_with_new_one()
        logger.info("New reference AIDE database setup successful.")

    def _run_cmd(self, cmd, check_exitcode=True):
        cmd_str = " ".join(cmd)
        logger.debug("Running '{}' command.".format(cmd_str))

        try:
            completed_proc = subprocess.run(cmd, check=check_exitcode,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            msg = "Failed to run '{}' command".format(cmd_str)
            raise ScannerError(msg, e) from e

        return completed_proc
