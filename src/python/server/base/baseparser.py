# -*- coding: utf-8 -*-
import abc
import argparse
import configparser

import common.constants
from server.multicastserver.error import MulticastServerParserError


class ConfigParser(metaclass=abc.ABCMeta):

    def __init__(self, config_path, config_section_name):
        self.options = {}
        self.config_path = config_path
        self.config_section_name = config_section_name

    @abc.abstractmethod
    def parse(self):
        pass

    def _load_config(self, parser):
        try:
            self.__load_config(parser)
        except (configparser.Error, FileNotFoundError) as e:
            msg = 'Loading server configuration failed. Details: {}'.format(e)
            raise MulticastServerParserError(msg, e)

    def __load_config(self, parser):
        root_parser = self._init_root_parser()
        args, remaining_argv = root_parser.parse_known_args()
        self.config_path = args.conf
        self._update_config_with_hardcoded_defaults()
        self._update_config_from_file()
        self._update_config_from_argv(root_parser, parser, remaining_argv)

    def _init_root_parser(self):
        # See: http://stackoverflow.com/q/3609852/1321680
        root_parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False)
        root_parser.add_argument(
            '-c', '--conf', metavar='FILE', default=self.config_path,
            help='custom configuration file path')
        return root_parser

    def _update_config_with_hardcoded_defaults(self):
        self.options = common.constants.DEFAULT_CONFIG

    def _update_config_from_file(self):
        parser = configparser.ConfigParser()
        parser.read(self.config_path)
        new_options = dict(parser.items(self.config_section_name))
        self._convert_number_string_values_to_int(new_options)
        self.options.update(new_options)

    def _update_config_from_argv(self, root_parser, parser, remaining_argv):
        wrapper_parser = argparse.ArgumentParser(
            parents=[root_parser, parser],
            epilog=common.constants.CONFIG_EPILOG)
        wrapper_parser.add_argument(
            '-v', '--verbose', action='count', default=0,
            help='increase output and log verbosity')
        wrapper_parser.add_argument(
            '--version', action='store_true',
            help='output version information and exit')
        wrapper_parser.set_defaults(**self.options)
        self.config = wrapper_parser.parse_args(remaining_argv)

    def _convert_number_string_values_to_int(self, options):
        # Without this function, there would be problem with -v option
        for key, val in options.items():
            if val.isdigit():
                options[key] = int(val)


def print_version(app_name, app_version):
    LICENSE = common.constants.LICENSE
    AUTHOR_NAME = common.constants.AUTHOR_NAME
    AUTHOR_EMAIL = common.constants.AUTHOR_EMAIL

    print('{} {}'.format(app_name, app_version))
    print(LICENSE.format(AUTHOR_NAME))
    print()
    print('Written by {} ({})'.format(AUTHOR_NAME, AUTHOR_EMAIL))
