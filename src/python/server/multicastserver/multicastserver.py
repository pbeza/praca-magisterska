# -*- coding: utf-8 -*-
import logging
import os
import time # TODO

from server.base import baseserver
from server.multicastserver import config
import server.multicastserver.constants as srvconstants

SERVER_NAME = 'multicast server'

logger = logging.getLogger(__name__)


class MulticastServer(baseserver.BaseServer):

    def __init__(self, config):
        super(MulticastServer, self).__init__(config, SERVER_NAME)

    @classmethod
    def from_file(cls, config_path, args):
        c = config.MulticastServerConfig(config_path,
                                         srvconstants.CONFIG_SECTION_NAME,
					 args)
        return cls(c)

    def run(self):
        super(MulticastServer, self).start_daemon()
        self._daemon_work()
        super(MulticastServer, self).stop_daemon()

    def _daemon_work(self):
        # global logger
        logger.info('This is TEST – start, PID: {}, PPID: {}'.format(os.getpid(),
                    os.getppid()))
        time.sleep(5)
        logger.info('This is TEST – stop')
