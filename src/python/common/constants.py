# -*- coding: utf-8 -*-
import logging

# Basic information about application, eg. license, author etc.

APP_VERSION = '0.1'
AUTHOR_NAME = 'Patryk Bęza'
AUTHOR_EMAIL = 'patryk.beza@gmail.com'
LICENSE = '''Copyright © 2017 {}
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.'''.format(AUTHOR_NAME)
CONFIG_EPILOG = '''This software is part of the master thesis project.  To
learn more about this implementation, refer project's white paper.'''

# Basic logger configuration, including logger format and log level used before
# loading logger configuration

BASIC_LOGGER_FORMAT = '[ %(levelname)s ] %(message)s'
BASIC_CONFIG_LOG_LEVEL = logging.NOTSET
APP_VERSION_FULL_TEMPLATE = '''{name} {version}
{license}

Written by {author} ({author_email})'''


def get_app_version(app_name):
    return APP_VERSION_FULL_TEMPLATE.format(
            name=app_name, version=APP_VERSION, license=LICENSE,
            author=AUTHOR_NAME, author_email=AUTHOR_EMAIL)
