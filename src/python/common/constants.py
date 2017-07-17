# -*- coding: utf-8 -*-

# Basic information about application, eg. license, author etc.

__version__ = "0.1"
__author__ = "Patryk Bęza"
__email__ = "bezap@student.mini.pw.edu.pl"
__license__ = '''Copyright © 2017 {}
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.'''.format(__author__)
APP_VERSION_FULL_TEMPLATE = '''{name} {version}
{license}

Written by {author} ({author_email})'''


def get_app_version(app_name):
    return APP_VERSION_FULL_TEMPLATE.format(
            name=app_name, version=__version__, license=__license__,
            author=__author__, author_email=__email__)


def print_version(app_name):
        print("{} {}".format(app_name, __version__))
        print(__license__.format(__author__))
        print()
        print("Written by {} ({})".format(__author__, __email__))
