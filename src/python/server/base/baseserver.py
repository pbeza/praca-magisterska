# -*- coding: utf-8 -*-
import daemon
import lockfile
import logging
import logging.config
import signal
import yaml

import common.constants
from server.base import baseconfig

logger = logging.getLogger(__name__)


# TODO TODO TODO
class BaseServer:

    def __init__(self, config, server_name):
        self.config = config
        self.server_name = server_name

    """@classmethod
    def from_file(cls, config_path, config_section_name, server_name):
        config = baseconfig.BaseServerConfig(config_path, config_section_name)
        return cls(config, server_name)"""

    def start_daemon(self, atexit_func=None):
        pid_file = self.get_pid_file_path()
        self.context = daemon.DaemonContext(
                pidfile=lockfile.FileLock(pid_file),
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
        self.context.open()
        self._setup_logger_config()
        logger.debug("Daemon successfully started ({})".format(
                     self.server_name))

    def stop_daemon(self):
        self.context.close()
        logger.debug("Daemon successfully stopped ({})".format(
                     self.server_name))

    def get_from_config(self, var_name):
        section_name = self.config.config_section_name
        return self.config.parser[section_name].get(var_name)

    def get_pid_file_path(self):
        return self.get_from_config(common.constants.CONF_VAR_PID_FILE_PATH)

    def get_logger_config_path(self):
        return self.get_from_config(common.constants.CONF_VAR_LOG_CONFIG_PATH)

    def _setup_logger_config(self):
        log_config_path = self.get_logger_config_path()
        with open(log_config_path) as f:
            log_config = yaml.load(f)
        try:
            logging.config.dictConfig(log_config)
        except ValueError as e:
            m = "Can't load logging configuration file read from '{}' "\
                "Details: {}".format(log_config_path, str(e))
            raise Exception(m) from e  # TODO
        global logger
        logger = logging.getLogger(__name__)

    def _signal_handler(self, signum, _):
        if signum == signal.SIGINT:
            logger.warning('SIGINT signal (num = {}) handled by {}',
                           signum, self.server_name)
        elif signum == signal.SIGTERM:
            logger.warning('SIGTERM signal (num = {}) handled by {}',
                           signum, self.server_name)
        else:
            logger.warning('Signal (num = {}) handled by {}',
                           signum, self.server_name)
