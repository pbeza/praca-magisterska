# -*- coding: utf-8 -*-
import logging
import re

from myscm.common.cmd import long_run_cmd, CommandLineError
from myscm.server.error import ServerError

logger = logging.getLogger(__name__)


class PackageManagerError(ServerError):
    pass


def get_file_debian_package_name_fallback(file_path):
    """Get package name of the given file path.

      dpkg-query is not able to find package name of uninstalled packages in
      opposite to apt-file (which is not installed by default). apt-file is
      much slower than dpkg-query -S."""

    cmd = ["apt-file", "search", "-l", file_path]
    msg = "to get package name of the file (`dpkg-query -S` fallback)"

    try:
        completed_proc = long_run_cmd(cmd, check_exitcode=False,
                                      suffix_msg=msg, debug_log=True)
    except CommandLineError as e:
        m = "Check if apt-file is installed and updated (run `apt update` if "\
            "needed)"
        raise PackageManagerError(m, e) from e

    if completed_proc.returncode:
        return "?"

    cmd_stdout = completed_proc.stdout.decode("utf-8").strip()
    pkg_names = cmd_stdout.split("\n")
    pkg_names_str = ",".join(pkg_names)

    return pkg_names_str


def get_file_debian_package_name(file_path):
    """Get Debian package name of the given file path."""

    cmd = ["dpkg-query", "-S", file_path]
    msg = "to get package Debian name of the file"
    completed_proc = long_run_cmd(cmd, check_exitcode=False, suffix_msg=msg,
                                  debug_log=True)

    if completed_proc.returncode:
        return get_file_debian_package_name_fallback(file_path)

    cmd_stdout = completed_proc.stdout.decode("utf-8").strip()
    detailed_pkg_names = cmd_stdout.split("\n")
    regex_str = r"(.*): .*"
    regex = re.compile(regex_str)
    pkg_names = []

    for pkg_name in detailed_pkg_names:
        pkg_name_match = regex.fullmatch(pkg_name)

        if not pkg_name_match or len(pkg_name_match.groups()) != 1:
            print(pkg_name)
            m = "Unexpected output of the '{}' command".format(" ".join(cmd))
            raise PackageManagerError(m)

        pkg_name_str = pkg_name_match.group(1)
        pkg_names.append(pkg_name_str)

    return ",".join(pkg_names)


def get_file_arch_package_name(file_path):
    """Get Arch Linux package name of the given file path."""

    cmd = ["pacman", "-Qo", file_path]

    msg = "to get package Arch Linux name of the file"
    completed_proc = long_run_cmd(cmd, check_exitcode=False, suffix_msg=msg,
                                  debug_log=True)

    if completed_proc.returncode:
        return "?"

    cmd_stdout = completed_proc.stdout.decode("utf-8").strip()
    detailed_pkg_names = cmd_stdout.split("\n")
    regex_str = r".* is owned by (.*) .*"
    regex = re.compile(regex_str)
    pkg_names = []

    for pkg_name in detailed_pkg_names:
        pkg_name_match = regex.fullmatch(pkg_name)

        if not pkg_name_match or len(pkg_name_match.groups()) != 1:
            print(pkg_name)
            m = "Unexpected output of the '{}' command".format(" ".join(cmd))
            raise PackageManagerError(m)

        pkg_name_str = pkg_name_match.group(1)
        pkg_names.append(pkg_name_str)

    return ",".join(pkg_names)


def get_file_package_name(file_path, server_config):
    package_getter_fun = None

    if server_config.distro_name.lower() == "debian":
        package_getter_fun = get_file_debian_package_name
    elif server_config.distro_name.lower() == "arch":
        package_getter_fun = get_file_arch_package_name
    else:
        m = "Package manager of your {} distribution is not supported"
        raise PackageManagerError(m)

    return package_getter_fun(file_path)
