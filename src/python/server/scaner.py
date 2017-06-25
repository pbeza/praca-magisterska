# -*- coding: utf-8 -*-
import logging
import subprocess

import server.config
from common.error import MySCMError

logger = logging.getLogger(__name__)


class ScanerError(MySCMError):
    pass


class Scaner:

    def __init__(self, aide_config):
        self.aide_config = aide_config

    def scan(self):
        """Scans system software and configuration using AIDE's --init
           option creating new reference AIDE database and renaming old one."""
        try:
            self._scan()
        except subprocess.CalledProcessError as e:
            msg = 'aide --init returned non-zero code - refer aide manual '\
                  'to learn more about status codes'
            raise ScanerError(msg, e) from e
        except server.config.ServerConfig as e:
            raise ScannerError('Server configuration error', e) from e

    def _scan(self):
        cmd = ['aide', '--init', '-c', self.aide_config.options.AIDE_config_file_path]
        logger.info("Running '{}' command".format(' '.join(cmd)))
        completed_proc = subprocess.run(cmd, check=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.aide_config.set_new_aide_reference_db()
        logger.info('New reference AIDE database setup successful')
