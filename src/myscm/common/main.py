# -*- coding: utf-8 -*-
import logging

from lockfile import LockError, UnlockError
from lockfile.pidlockfile import PIDLockFile

import myscm.common.error
import myscm.common.parser

logger = logging.getLogger(__name__)


def _get_app_config(config_parser, config_path, section_name):
    config = None

    try:
        parser = config_parser(config_path, section_name)
        config = parser.parse()
    except myscm.common.parser.ParserError as e:
        raise myscm.common.parser.ParserError("Parsing error", e) from e

    config.set_log_level(logger)

    logger.debug("Supported {} GNU/Linux distribution detected."
                 .format(config.distro_name.title()))
    logger.debug("Server configuration: {}.".format(vars(config.options)))

    return config


def _run_single_instance_app(main_fun, config):
    try:
        with PIDLockFile(config.options.PID_lock_file_path, timeout=0) as lock:
            main_fun(config)
            assert lock.is_locked()
    except (LockError, UnlockError) as e:
        logger.error("Can't run two instances of the application at the same "
                     "time. Error details: {}.".format(e))


def run_main(main_fun, config_parser_class, config_path, config_section_name):
    exit_code = 0

    try:
        config = _get_app_config(config_parser_class, config_path,
                                 config_section_name)
        _run_single_instance_app(main_fun, config)
    except (KeyboardInterrupt, EOFError):
        logger.info("Keyboard interrupt or EOF detected. Exiting.")
    except myscm.common.error.MySCMError as e:
        logger.error(e)
        exit_code = 1
    except Exception as e:
        logger.exception("Unexpected exception handled in {}. "
                         "Details: {}.".format(__name__, str(e)))
        exit_code = 1

    return exit_code
