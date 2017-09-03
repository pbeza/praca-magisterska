#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management client
   application (myscm-cli)."""

import logging
import os
import progressbar
import sys

from myscm.client.parser import ClientConfigParser
from myscm.client.sysimgextractor import SysImgExtractor
from myscm.client.sysimgmanager import SysImgManager
from myscm.client.sysimgupdater import SysImgUpdater
from myscm.common.signaturemanager import SignatureManager
import myscm.common
import myscm.common.main

logger = logging.getLogger("myscm.client")

CLI_CONFIG_PATH = "myscm/client/config/config.ini"
CLI_SECTION_NAME = "myscm-cli"


def _main(config):
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
        updater = SysImgUpdater(config)
        updater.update()
    elif config.options.upgrade_sys_img:
        updater = SysImgUpdater(config)
        sys_img_path = updater.update()
        if sys_img_path is not None:
            sys_img_fname = os.path.basename(sys_img_path)
            sys_img_manager = SysImgManager(config)
            if isinstance(config.options.upgrade_sys_img, bool):
                ver = sys_img_manager.get_target_sys_img_ver_from_fname(sys_img_fname)
            else:
                ver = config.options.upgrade_sys_img
            config.options.apply_img = ver
            sys_img_extractor = SysImgExtractor(config)
            sys_img_extractor.apply_sys_img()
    elif config.options.verify_sys_img:
        sys_img_manager = SysImgManager(config)
        sys_img_manager.verify_sys_img()
    elif config.options.list_sys_img:
        sys_img_manager = SysImgManager(config)
        sys_img_manager.print_all_verified_img_paths_sorted()
    elif config.options.config_check:
        # If check fails, then Exception is raised and caught in __main__
        print("Configuration OK")
    elif config.options.print_sys_img_ver:
        manager = SysImgManager(config)
        manager.print_current_system_state_version()
    elif config.options.verify_file:
        signature_path = config.options.verify_file[0]
        path_to_verify = config.options.verify_file[1]
        ssl_pub_key_path = config.options.SSL_cert_public_key_path
        m = SignatureManager()
        valid = m.ssl_verify(path_to_verify, signature_path, ssl_pub_key_path)
        print("SSL signature {}valid".format("" if valid else "in"))
    else:
        logger.info(myscm.common.constants.APP_NEED_OPTION_TO_RUN_MSG)


if __name__ == "__main__":
    exit_code = myscm.common.main.run_main(_main, ClientConfigParser,
                                           CLI_CONFIG_PATH, CLI_SECTION_NAME)
    progressbar.streams.flush()  # progressbar2 hotfix if exception
    sys.exit(exit_code)
