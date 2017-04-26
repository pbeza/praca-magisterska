#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main starting point for multicasting server application.  This server
regularly sends configuration to clients using PGM multicast protocol."""

import logging

from server.multicastserver.multicastserver import MulticastServer
import common.constants
import common.myscmerror as error
import server.multicastserver.config as srvconfig

logger = logging.getLogger(__name__)


def _main():
    # Temporary logger before loading logger config file
    logging.basicConfig(
        format=common.constants.BASIC_LOGGER_FORMAT,
        level=common.constants.BASIC_CONFIG_LOG_LEVEL)
    srvconfig.init()
    srv = MulticastServer(srvconfig.config)
    srv.run()


if __name__ == '__main__':
    try:
        _main()
    except error.MySCMError as e:
        logger.error(str(e))
    except (KeyboardInterrupt, EOFError):
        logger.info('Keyboard interrupt or EOF detected')
    except Exception as e:
        logger.exception('Unexpected exception handled in {}. '
                         'Details: {}'.format(__name__, str(e)))
