# -*- coding: utf-8 -*-
import logging
import re

from common.cmd import long_run_cmd
from common.error import MySCMError

logger = logging.getLogger(__name__)


class PackageManagerError(MySCMError):
    pass


def get_file_debian_package_name(file_path):
    # apt-file is alternative to dpkg-query (but it's much slower)
    file_path = "/bin/ls"
    cmd = ["dpkg-query", "-S", file_path]
    msg = " to get package name of the file"
    completed_proc = long_run_cmd(cmd, check_exitcode=False, suffix_msg=msg,
                                  debug_log=True)

    if completed_proc.returncode:
        return "?"

    regex_str = r"(.*): .*\n"
    regex = re.compile(regex_str)
    cmd_stdout = completed_proc.stdout.decode("utf-8")
    pkg_names_match = regex.fullmatch(cmd_stdout)

    if not pkg_names_match or len(pkg_names_match.groups()) != 1:
        m = "Unexpected output of the '{}' command".format(" ".join(cmd))
        raise PackageManagerError(m)

    pkg_names_str = pkg_names_match.group(1)
    pkg_names = pkg_names_str.replace(" ", "")

    return pkg_names


def get_file_package_name(file_path, server_config):
    package_getter_fun = None

    if server_config.distro_name.lower() == "debian":  # TODO Linux Arch
        package_getter_fun = get_file_debian_package_name
    else:
        m = "Package manager of your {} distribution is not supported"
        raise PackageManagerError(m)

    return package_getter_fun(file_path)
