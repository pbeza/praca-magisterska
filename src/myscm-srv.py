#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management server
   application (myscm-srv)."""

import logging
import os
import progressbar
import sys

from myscm.common.signaturemanager import SignatureManager
from myscm.server.aidedbmanager import AIDEDatabasesManager
from myscm.server.parser import ServerConfigParser
from myscm.server.scanner import Scanner
from myscm.server.sysimggenerator import SystemImageGenerator
from myscm.server.sysimgmanager import SysImgManager
import myscm.common
import myscm.common.constants
import myscm.common.main

logger = logging.getLogger("myscm.server")

SRV_CONFIG_PATH = "myscm/server/config/config.ini"
SRV_SECTION_NAME = "myscm-srv"


def _main(config):
    if os.geteuid() != 0:
        m = "This application is supposed to be ran with root permissions. "\
            "Root permissions may be not needed if you don't need to scan "\
            "restricted parts of the filesystem."
        logger.warning(m)

    if config.options.version:
        myscm.common.print_version()
    elif config.options.scan:
        scanner = Scanner(config)
        scanner.scan()
    elif config.options.gen_img is not None:  # explicit check since can be 0
        sys_img_generator = SystemImageGenerator(config)
        sys_img_generator.generate_img()
    elif config.options.config_check:
        # If check fails, then Exception is raised and caught in __main__
        print("Configuration OK")
    elif config.options.list_databases:
        manager = AIDEDatabasesManager(config)
        manager.print_all_aide_db_paths_sorted()
    elif config.options.list_sys_img:
        manager = SysImgManager(config)
        manager.print_all_verified_img_paths_sorted()
    elif config.options.upgrade is not None:  # explicit check since can be 0
        scanner = Scanner(config)
        scanner.scan()
        config.options.gen_img = config.options.upgrade
        sys_img_generator = SystemImageGenerator(config)
        sys_img_generator.generate_img()
    elif config.options.sign_file:
        m = SignatureManager()
        path_to_sign = config.options.sign_file
        signature_path = path_to_sign + SignatureManager.SIGNATURE_EXT
        priv_key = config.options.SSL_cert_priv_key_path
        m.ssl_sign(path_to_sign, signature_path, priv_key)
    elif config.options.verify_file != (None, None):
        signature_path = config.options.verify_file[0]
        path_to_verify = config.options.verify_file[1]
        ssl_pub_key_path = config.options.SSL_cert_public_key_path
        m = SignatureManager()
        valid = m.ssl_verify(path_to_verify, signature_path, ssl_pub_key_path)
        print("SSL signature {}valid".format("" if valid else "in"))
    else:
        logger.info(myscm.common.constants.APP_NEED_OPTION_TO_RUN_MSG)


if __name__ == "__main__":
    exit_code = myscm.common.main.run_main(_main, ServerConfigParser,
                                           SRV_CONFIG_PATH, SRV_SECTION_NAME)
    progressbar.streams.flush()  # progressbar2 hotfix if exception
    sys.exit(exit_code)