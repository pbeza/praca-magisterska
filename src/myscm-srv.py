#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management server
   application (myscm-srv)."""

import logging
import os
import progressbar
import sys

import myscm.common
import myscm.common.constants
import myscm.common.main
from myscm.server.aidedbmanager import AIDEDatabasesManager
from myscm.server.parser import ServerConfigParser
from myscm.server.scanner import Scanner, ScannerError
from myscm.server.sysimggenerator import SystemImageGenerator
from myscm.server.sysimggenerator import SystemImageGeneratorError
from myscm.server.sysimgmanager import SysImgManager

logger = logging.getLogger("myscm.server")

SRV_CONFIG_PATH = "myscm/server/config/config.ini"
SRV_SECTION_NAME = "myscm-srv"


def get_app_config():
    app_config = myscm.common.main.get_app_config(ServerConfigParser,
                                                  SRV_CONFIG_PATH,
                                                  SRV_SECTION_NAME)
    return app_config


def scan(config):
    try:
        scanner = Scanner(config)
        scanner.scan()
    except ScannerError as e:
        raise ScannerError("AIDE --init wrapper error", e) from e


def gen_img(config):
    try:
        sys_img_generator = SystemImageGenerator(config)
        sys_img_generator.generate_img()
    except SystemImageGeneratorError as e:
        m = "Reference system image generator error"
        raise SystemImageGeneratorError(m, e) from e


def _main():
    config = get_app_config()

    if os.geteuid() != 0:
        m = "This application is supposed to be ran with root permissions. "\
            "Root permissions may be not needed if you don't need to scan "\
            "restricted parts of the filesystem."
        logger.warning(m)

    if config.options.version:
        myscm.common.print_version()
    elif config.options.scan:
        scan(config)
    elif config.options.gen_img is not None:  # explicit check since can be 0
        gen_img(config)
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
        scan(config)
        config.options.gen_img = config.options.upgrade
        gen_img(config)
    else:
        logger.info(myscm.common.constants.APP_NEED_OPTION_TO_RUN_MSG)


if __name__ == "__main__":
    exit_code = myscm.common.main.run_main(_main)
    progressbar.streams.flush()  # progressbar2 bug if app ends with exception
    sys.exit(exit_code)
