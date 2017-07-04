# -*- coding: utf-8 -*-
from lockfile.pidlockfile import PIDLockFile
import lockfile
import daemon
import logging
import logging.config
import os
import signal

from common.error import MySCMError

logger = logging.getLogger(__name__)


class ServerError(MySCMError):
    pass


class BaseServer:

    def __init__(self, config, server_name):
        self.config = config
        self.server_name = server_name

    def _get_file_descriptors_to_preserve(self):
        global logger
        tmp_log = logger
        preserve_list = []
        while tmp_log.name != "root":
            for h in tmp_log.handlers:
                if isinstance(h, logging.FileHandler):
                    preserve_list.append(h.stream.fileno())
            tmp_log = tmp_log.parent
        return preserve_list

    def start_daemon(self, atexit_func=None):
        files_to_preserve = self._get_file_descriptors_to_preserve()
        logger.debug("Log file descriptors to preserve after daemonization: "
                     "{}.".format(files_to_preserve))
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
        #     signal.SIGHUP: "terminate",
        #     signal.SIGUSR1: reload_program_config,
        #     signal.SIGTTIN : None
        #     signal.SIGTTOU : None
        #     signal.SIGTSTP : None
        #     signal.SIGTERM: program_cleanup,
        #     signal.SIGTERM : "terminate"
        # }
        # interesting_file = open("eggs.data", "w")
        # self.context.files_preserve = [important_file, interesting_file]
        if atexit_func is not None:
            daemon.register_atexit_function(atexit_func)
        logger.debug("Starting daemon. All subsequent log messages will be "
                     "redirected to syslog and log file unless custom log "
                     "configuration was set.")
        try:
            self.context.open()
        except lockfile.AlreadyLocked as e:
            m = "Server is probably already running. PID lock file exists"
            raise ServerError(m, e) from e
        logger.debug("Daemon '{}' successfully started.".format(
                     self.server_name))

    def stop_daemon(self):
        self.context.close()
        logger.debug("Daemon '{}' successfully stopped.".format(
                     self.server_name))

    def terminate_daemon(self):
        m = "Terminating existing daemon based on PID lock file '{}'."\
              .format(self.config.PID_file_path)
        logger.info(m)
        pid = lockfile.pidlockfile.read_pid_from_pidfile(
                self.config.PID_file_path)
        if pid is None:
            m = "Can't stop daemon because PID lock file '{}' doesn't "\
                  "exist.".format(self.config.PID_file_path)
            raise ServerError(m)

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            m = "Sending SIGTERM signal to daemon with PID = {} has failed."\
                  .format(pid)
            raise ServerError(m)

        lockfile.pidlockfile.break_lock(self.config.PID_file_path)

    def _signal_handler(self, signum, _):
        sigdict = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}
        signame = sigdict.get(signum, "Unhandled")
        logger.warning("{} signal (num = {}) handled by {}.".format(
                       signame, signum, self.server_name))


# class MulticastServer(server.base.baseserver.BaseServer):
#
#     def __init__(self, config):
#         super().__init__(config, SERVER_NAME)
#
#     def run(self):
#         try:
#             super().start_daemon()
#             self._daemon_work()
#             super().stop_daemon()
#         except server.base.baseserver.ServerError as e:
#             m = "Multicast server daemon failed with error: {}.".format(e)
#             logger.error(m)
#             raise MulticastServerError(m, e) from e
#         except Exception as e:
#             logger.exception("Ups! Daemon failed. Details: {}.".format(e))
#             raise
#
#     def terminate(self):
#         super().terminate_daemon()
#
#     def _daemon_work(self):
#         # global logger
#         logger.info("This is TEST - start, PID: {}, PPID: {}.".format(
#                     os.getpid(), os.getppid()))
#         time.sleep(35)
#         logger.info("This is TEST - stop.")
