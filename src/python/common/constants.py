# -*- coding: utf-8 -*-

# Basic information about application, eg. license, author etc.

APP_VERSION = "0.1"
AUTHOR_NAME = "Patryk Bęza"
AUTHOR_EMAIL = "bezap@student.mini.pw.edu.pl"
LICENSE = '''Copyright © 2017 {}
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.'''.format(AUTHOR_NAME)
APP_VERSION_FULL_TEMPLATE = '''{name} {version}
{license}

Written by {author} ({author_email})'''


def get_app_version(app_name):
    return APP_VERSION_FULL_TEMPLATE.format(
            name=app_name, version=APP_VERSION, license=LICENSE,
            author=AUTHOR_NAME, author_email=AUTHOR_EMAIL)


def print_version(app_name):
        print("{} {}".format(app_name, APP_VERSION))
        print(LICENSE.format(AUTHOR_NAME))
        print()
        print("Written by {} ({})".format(AUTHOR_NAME, AUTHOR_EMAIL))
