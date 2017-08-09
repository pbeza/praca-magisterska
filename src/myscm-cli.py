#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management client
   application (myscm-cli)."""

import logging
import os
import progressbar
import sys

import myscm.common
import myscm.common.main
from myscm.client.parser import ClientConfigParser
from myscm.client.sysimgextractor import SysImgExtractor
from myscm.client.sysimgmanager import SysImgManager

logger = logging.getLogger("myscm")

CLI_CONFIG_PATH = "myscm/client/config/config.ini"
CLI_SECTION_NAME = "myscm-cli"


def get_app_config():
    app_config = myscm.common.main.get_app_config(ClientConfigParser,
                                                  CLI_CONFIG_PATH,
                                                  CLI_SECTION_NAME)
    return app_config


def _main():
    config = get_app_config()

    if os.geteuid() != 0:
        m = "This application is supposed to be ran with root permissions. "\
            "Root permissions may be not needed if you don't need to apply "\
            "myscm system image that modifies restricted files."
        logger.warning(m)

    if config.options.version:
        myscm.common.print_version()
    elif config.options.apply_img is not None:  # explicit check since can be 0
        sys_img_extractor = SysImgExtractor(config)
        sys_img_extractor.apply_sys_img()
    elif config.options.update_sys_img:
        logger.debug("--update option is not implemented yet")  # TODO
    elif config.options.upgrade_sys_img:
        logger.debug("--upgrade option is not implemented yet")  # TODO
    elif config.options.verify_sys_img:
        sys_img_manager = SysImgManager(config)
        sys_img_manager.verify_sys_img()
    elif config.options.force_apply:
        logger.debug("--force is not implemented yet")  # TODO
    elif config.options.list_sys_img:
        sys_img_manager = SysImgManager(config)
        sys_img_manager.print_all_verified_img_paths_sorted()
    elif config.options.config_check:
        # If check fails, then Exception is raised and caught in __main__
        print("Configuration OK")
    elif config.options.print_sys_img_ver:
        manager = SysImgManager(config)
        manager.print_current_system_state_version()
    else:
        logger.info(myscm.common.constants.APP_NEED_OPTION_TO_RUN_MSG)


if __name__ == "__main__":
    exit_code = myscm.common.main.run_main(_main)
    progressbar.streams.flush()  # progressbar2 bug if app ends with exception
    sys.exit(exit_code)
