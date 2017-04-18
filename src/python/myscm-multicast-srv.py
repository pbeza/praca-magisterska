#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main starting point for multicasting server application.  This server
regularly sends configuration to clients using PGM multicast protocol."""

import logging

import server.multicastserver.config as srvconfig
import server.multicastserver.error as srverror

logger = logging.getLogger(__name__)


def _main():
    srvconfig.init()
    if srvconfig.config.version:
        srvconfig.config_parser.print_version()


if __name__ == '__main__':

    # Setup temporary logger before loading final logger configuration
    logging.basicConfig(format='%(message)s', level=logging.NOTSET)

    try:
        _main()
    except srverror.MulticastServerError as e:
        logger.warning(e)
        if srvconfig.config and srvconfig.config.verbose > 0:
            logger.warning(e.get_details())
    except (KeyboardInterrupt, EOFError):
        logger.info('Keyboard interrupt or EOF detected')
    except Exception as e:
        logger.exception('Unexpected exception handled in {}. '
                         'Details: {}'.format(__name__, str(e)))
