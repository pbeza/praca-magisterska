# -*- coding: utf-8 -*-

import argparse

from server.base import baseparser
from server.multicastserver import config
import server.multicastserver.constants


class MulticastServerConfigParser(baseparser.ConfigParser):

    def __init__(self, config_path, config_section_name):
        super(MulticastServerConfigParser, self).__init__(config_path,
                                                          config_section_name)
        self.parser = self._init_parser()

    def _init_parser(self):
        parser = argparse.ArgumentParser(
            add_help=False,
            description='''This is multicast server side of the mySCM
                           application – simple Software Configuration
                           Management (SCM) tool for managing clients running
                           Debian and Arch Linux based distributions.  This
                           server is intended to send configuration to all the
                           clients using PGM protocol.''')
        parser.add_argument('-m', '--mtest', action='store_true', help='test!')
        return parser

    def parse(self):
        self._load_config(self.parser)
        return config.MulticastServerConfig(vars(self.config))


def print_version():
    baseparser.print_version(server.multicastserver.constants.APP_NAME,
                             server.multicastserver.constants.APP_VERSION)
