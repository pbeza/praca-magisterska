#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management server
   application (myscm-srv)."""

import logging
import sys

import common
import common.constants
import common.main
from server.aidedbmanager import AIDEDatabasesManager
from server.parser import ServerConfigParser
from server.scanner import Scanner, ScannerError
from server.sysimggenerator import SystemImageGenerator
from server.sysimggenerator import SystemImageGeneratorError
from server.sysimgmanager import SysImgManager

logger = logging.getLogger("server")

SRV_CONFIG_PATH = "server/config/config.ini"
SRV_SECTION_NAME = "myscm-srv"


def get_app_config():
    app_config = common.main.get_app_config(ServerConfigParser,
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

    if config.options.version:
        common.print_version()
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
        logger.info(common.constants.APP_NEED_OPTION_TO_RUN_MSG)


if __name__ == "__main__":
    exit_code = common.main.run_main(_main)

    import progressbar
    progressbar.streams.flush()  # probably progressbar2 bug

    sys.exit(exit_code)
