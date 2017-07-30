# -*- coding: utf-8 -*-
import logging

import common.error
import common.parser

logger = logging.getLogger(__name__)


def get_app_config(config_parser, config_path, section_name):
    config = None

    try:
        parser = config_parser(config_path, section_name)
        config = parser.parse()
    except common.parser.ParserError as e:
        raise common.parser.ParserError("Parsing error", e) from e

    config.set_log_level(logger)

    logger.debug("Supported {} GNU/Linux distribution detected."
                 .format(config.distro_name.title()))
    logger.debug("Server configuration: {}.".format(vars(config.options)))

    return config


def run_main(main_fun):
    exit_code = 0

    try:
        main_fun()
    except (KeyboardInterrupt, EOFError):
        logger.info("Keyboard interrupt or EOF detected. Exiting.")
    except common.error.MySCMError as e:
        logger.error(e)
        exit_code = 1
    except Exception as e:
        logger.exception("Unexpected exception handled in {}. "
                         "Details: {}.".format(__name__, str(e)))
        exit_code = 1

    return exit_code
