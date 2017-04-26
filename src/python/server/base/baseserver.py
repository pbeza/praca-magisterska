# -*- coding: utf-8 -*-
from lockfile.pidlockfile import PIDLockFile
import lockfile
import daemon
import logging
import logging.config
import signal

from common.myscmerror import MySCMError

logger = logging.getLogger(__name__)


class BaseServer:

    def __init__(self, config, server_name):
        self.config = config
        self.server_name = server_name

    def _get_file_descriptors_to_preserve(self):
        global logger
        tmp_log = logger
        preserve_list = []
        while tmp_log.name != 'root':
            for h in tmp_log.handlers:
                if isinstance(h, logging.FileHandler):
                    preserve_list.append(h.stream.fileno())
            tmp_log = tmp_log.parent
        return preserve_list

    def start_daemon(self, atexit_func=None):
        files_to_preserve = self._get_file_descriptors_to_preserve()
        logger.debug('Log file descriptors to preserve after daemonization: '
                     '{}'.format(files_to_preserve))
        self.context = daemon.DaemonContext(
                pidfile=PIDLockFile(self.config.PID_file_path),
                files_preserve=files_to_preserve,
                detach_process=True,
                signal_map={
                    signal.SIGINT:  self._signal_handler,
                    signal.SIGTERM: self._signal_handler
                }
            )
        # self.context.signal_map = {
        #     signal.SIGHUP: 'terminate',
        #     signal.SIGUSR1: reload_program_config,
        #     signal.SIGTTIN : None
        #     signal.SIGTTOU : None
        #     signal.SIGTSTP : None
        #     signal.SIGTERM: program_cleanup,
        #     signal.SIGTERM : 'terminate'
        # }
        # interesting_file = open('eggs.data', 'w')
        # self.context.files_preserve = [important_file, interesting_file]
        if atexit_func is not None:
            daemon.register_atexit_function(atexit_func)
        logger.debug('Before daemonization')
        logger.debug('h: {}'.format(vars(logger.parent)))
        try:
            self.context.open()
        except (FileExistsError, lockfile.AlreadyLocked) as e:
            logger.error('dupa')
            msg = 'Server is already running – PID file exists'
            raise ServerError(msg, e) from e
        logger.debug("Daemon '{}' successfully started".format(
                     self.server_name))

    def stop_daemon(self):
        self.context.close()
        logger.debug("Daemon '{}' successfully stopped".format(
                     self.server_name))

    def _signal_handler(self, signum, _):
        sigdict = {signal.SIGINT: 'SIGINT', signal.SIGTERM: 'SIGTERM'}
        signame = sigdict.get(signum, 'Unhandled')
        logger.warning('{} signal (num = {}) handled by {}'.format(
                       signame, signum, self.server_name))


class ServerError(MySCMError):
    pass
