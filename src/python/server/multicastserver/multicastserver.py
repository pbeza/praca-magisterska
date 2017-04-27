# -*- coding: utf-8 -*-
import logging
import os
import time  # TODO

import server.base.baseserver

SERVER_NAME = 'multicast server'

logger = logging.getLogger(__name__)


class MulticastServer(server.base.baseserver.BaseServer):

    def __init__(self, config):
        super().__init__(config, SERVER_NAME)

    def run(self):
        try:
            super().start_daemon()
            self._daemon_work()
            super().stop_daemon()
        except server.base.baseserver.ServerError as e:
            msg = 'Multicast server daemon failed with error: {}'.format(e)
            logger.error(msg)
            raise MulticastServerError(msg, e) from e
        except Exception as e:
            logger.exception('Ups! Daemon failed. Details: {}'.format(e))
            raise

    def terminate(self):
        super().terminate_daemon()

    def _daemon_work(self):
        # global logger
        logger.info('This is TEST - start, PID: {}, PPID: {}'.format(
                    os.getpid(), os.getppid()))
        time.sleep(35)
        logger.info('This is TEST - stop')


class MulticastServerError(server.base.baseserver.ServerError):
    pass
