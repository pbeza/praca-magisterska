#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main starting point for My Software Configuration Management server
   application (myscm-srv)."""

import logging

import common
import server.error
from server.parser import ServerConfigParser, ServerParserError
from server.scaner import Scaner, ScanerError

logger = logging.getLogger('server')


def get_app_config():
    config = None

    try:
        parser = ServerConfigParser('config.ini', 'myscm-srv')
        config = parser.parse()
    except ServerParserError as e:
        raise ServerParserError('Parsing error', e) from e

    if config.options.verbose > 1:
        logger.debug('Loaded server configuration: {}.'
                     .format(vars(config.options)))

    return config


def _main():
    config = get_app_config()

    if config.options.version:
        common.print_version()
        return

    try:
        scaner = Scaner(config)
        scaner.scan()
    except ScanerError as e:
        raise ScanerError('AIDE scaner wrapper error', e) from e


if __name__ == '__main__':
    try:
        _main()
    except (KeyboardInterrupt, EOFError):
        logger.info('Keyboard interrupt or EOF detected')
    except common.error.MySCMError as e:
        logger.error(e)
    except Exception as e:
        logger.exception('Unexpected exception handled in {}. '
                         'Details: {}'.format(__name__, str(e)))
