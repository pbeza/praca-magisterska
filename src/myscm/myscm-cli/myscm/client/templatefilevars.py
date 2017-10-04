# -*- coding: utf-8 -*-


def get_templates_vars():
    return VARS_MAPPIG


def _get_hostname():
    import socket
    return socket.gethostname()


def _get_username():
    import getpass
    return getpass.getuser()


def _get_userid():
    username = _get_username()
    import pwd
    return str(pwd.getpwnam(username).pw_uid)


def _get_unix_time():
    import time
    return str(int(time.time()))


def _get_home_dir():
    from pathlib import Path
    return str(Path.home())


VARS_MAPPIG = {
    "HOSTNAME": _get_hostname,
    "USERNAME": _get_username,
    "USER_ID": _get_userid,
    "HOME": _get_home_dir,
    "UNIX_TIME": _get_unix_time
}
