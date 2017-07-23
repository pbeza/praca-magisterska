# -*- coding: utf-8 -*-
import logging
import subprocess

from common.error import MySCMError

logger = logging.getLogger(__name__)


class CommandLineError(MySCMError):
    pass


def long_run_cmd(cmd, check_exitcode=True, stdout_opt=subprocess.PIPE,
                 stderr_opt=subprocess.STDOUT):
    suffix_msg = "Please wait - it may take some time to finish..."
    run_cmd(cmd, check_exitcode, stdout_opt, stderr_opt, suffix_msg)


def run_cmd(cmd, check_exitcode=True, stdout_opt=subprocess.PIPE,
            stderr_opt=subprocess.STDOUT, suffix_msg=None):
    """Run specified command and optionally check exit code for error."""

    cmd_str = " ".join(cmd)
    suffix_msg = " {}".format(suffix_msg) if suffix_msg else ""
    logger.info("Running '{}' command.{}".format(cmd_str, suffix_msg))

    try:
        completed_proc = subprocess.run(cmd, check=check_exitcode,
                                        stdout=stdout_opt, stderr=stderr_opt)
    except subprocess.CalledProcessError as e:
        m = "Failed to run '{}' command".format(cmd_str)
        raise CommandLineError(m, e) from e

    if completed_proc.stderr:
        m = "stderr output for '{}' command: '{}'.".format(
             cmd_str, completed_proc.stderr.decode("utf-8"))
        logger.warning(m)

    return completed_proc
