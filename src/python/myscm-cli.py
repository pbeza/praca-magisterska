#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management client
   application (myscm-cli)."""

import logging
import sys

import common
import common.main
from client.parser import ClientConfigParser
from client.sysimgmanager import SysImgManager

logger = logging.getLogger("client")

CLI_CONFIG_PATH = "client/config/config.ini"
CLI_SECTION_NAME = "myscm-cli"


def get_app_config():
    app_config = common.main.get_app_config(ClientConfigParser,
                                            CLI_CONFIG_PATH,
                                            CLI_SECTION_NAME)
    return app_config


def _main():
    config = get_app_config()

    if config.options.version:
        common.print_version()
    elif config.options.apply_img is not None:  # explicit check since can be 0
        logger.debug("--apply-img option is not implemented yet")  # TODO
    elif config.options.update_sys_img:
        logger.debug("--update option is not implemented yet")  # TODO
    elif config.options.upgrade_sys_img:
        logger.debug("--upgrade option is not implemented yet")  # TODO
    elif config.options.verify_sys_img:
        logger.debug("--verify-img option is not implemented yet")  # TODO
    elif config.options.force_apply:
        logger.debug("--force is not implemented yet")  # TODO
    elif config.options.list_sys_img:
        sys_img_manager = SysImgManager(config)
        sys_img_manager.print_all_verified_img_paths_sorted()
    elif config.options.config_check:
        # If check fails, then Exception is raised and caught in __main__
        print("Configuration OK")
    else:
        logger.info(common.constants.APP_NEED_OPTION_TO_RUN_MSG)


if __name__ == "__main__":
    exit_code = common.main.run_main(_main)
    sys.exit(exit_code)
