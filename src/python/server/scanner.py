# -*- coding: utf-8 -*-
import logging

from common.cmd import CommandLineError
from common.cmd import run_cmd
from server.aidedbmanager import AIDEDatabasesManager
from server.aidedbmanager import AIDEDatabasesManagerError
from server.error import ServerError

logger = logging.getLogger(__name__)


class ScannerError(ServerError):
    pass


class Scanner:

    def __init__(self, server_config):
        self.server_config = server_config
        self.aide_db_manager = AIDEDatabasesManager(self.server_config)

    def scan(self):
        """Scan system software and configuration using AIDE's --init option
           creating new reference AIDE database and renaming old one."""

        if self._is_reference_aide_db_outdated():
            try:
                self._scan()
            except CommandLineError as e:
                raise ScannerError("Error executing AIDE's command", e) from e
            except AIDEDatabasesManagerError as e:
                raise ScannerError("AIDE's databases manager error", e) from e
        else:
            m = "Current reference AIDE database '{}' is up-to-date. No need "\
                "to create new database. I have nothing to do - exiting."\
                .format(self.server_config.aide_reference_db_path)
            logger.info(m)

    def _is_reference_aide_db_outdated(self):
        """Return True if reference AIDE database aide.db is outdated."""

        logger.info("Running AIDE --check. It may take some time...")

        cmd = [
            "aide", "--check", "-c",
            self.server_config.options.AIDE_config_path
        ]
        completed_proc = run_cmd(cmd, False)
        uptodate_msg = "AIDE found NO differences between database and "\
                       "filesystem. Looks okay!!"
        return uptodate_msg not in completed_proc.stdout.decode("utf-8")

    def _scan(self):
        """Scan system looking for changes, replace old aide.db with new one
           and move old aide.db to aide.db.X (X is incremented integer)."""

        logger.info("Running AIDE --init. It may take some time...")

        cmd = [
            "aide", "--init", "-c",
            self.server_config.options.AIDE_config_path
        ]
        run_cmd(cmd, True)
        self.aide_db_manager.replace_old_aide_db_with_new_one()
        logger.info("New reference AIDE database setup successful.")
