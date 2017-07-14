#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""Main starting point for My Software Configuration Management server
   application (myscm-srv)."""

import logging
import sys

import common
from server.parser import ServerConfigParser, ServerParserError
from server.scanner import Scanner, ScannerError
from server.sysimggenerator import SystemImageGenerator, SystemImageGeneratorError

logger = logging.getLogger("server")


def get_app_config():
    config = None

    try:
        parser = ServerConfigParser("config.ini", "myscm-srv")
        config = parser.parse()
    except ServerParserError as e:
        raise ServerParserError("Parsing error", e) from e

    if config.options.verbose > 1:
        logger.debug("Loaded server configuration: {}."
                     .format(vars(config.options)))

    return config


def _main():
    config = get_app_config()

    if config.options.version:
        common.print_version()
    elif config.options.scan:
        _scan(config)
    elif config.options.gen_img is not None:  # Note that 0 is valid argument
        _gen_img(config)
    elif config.options.config_check:
        logger.debug("Configuration check ended successfully")
        # If check fails, then Exception is raised and caught in __main__
    else:
        logger.info("This application does nothing unless you specify what "
                    "it should do. See --help to learn more.")


def _scan(config):
    try:
        scanner = Scanner(config)
        scanner.scan()
    except ScannerError as e:
        raise ScannerError("AIDE scanner wrapper error", e) from e


def _gen_img(config):
    try:
        sys_img_generator = SystemImageGenerator(config)
        sys_img_generator.generate_img()
    except SystemImageGeneratorError as e:
        m = "Reference system image generator error"
        raise SystemImageGeneratorError(m, e) from e


if __name__ == "__main__":
    exit_code = 0

    try:
        _main()
    except (KeyboardInterrupt, EOFError):
        logger.info("Keyboard interrupt or EOF detected.")
    except common.error.MySCMError as e:
        logger.error(e)
        exit_code = 1
    except Exception as e:
        logger.exception("Unexpected exception handled in {}. "
                         "Details: {}.".format(__name__, str(e)))
        exit_code = 1

    sys.exit(exit_code)
