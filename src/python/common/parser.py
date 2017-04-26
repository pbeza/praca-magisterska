# -*- coding: utf-8 -*-
from argparse import HelpFormatter
from operator import attrgetter
import argparse
import configparser
import os

from common.myscmerror import MySCMError
import common.constants


class ConfigOption:
    """App's config option base class."""

    def __init__(self, name, value, validator):
        self.name = name
        self.value = value
        self.validator = validator

    def assert_valid(self, value=None):
        if value is None:
            value = self.value
        if self.validator is not None:
            self.validator(value)


class ArgsConfigOption(ConfigOption):
    """App's config option specified as a CLI argument."""

    def __init__(self, name, value, validator, *args, **kwargs):
        super().__init__(name, value, validator)
        self.args = args
        self.kwargs = kwargs
        # Use the same names for both config read from CLI and file to allow to
        # override options read from file with options read from CLI
        self.kwargs.update(dest=name)


class FileConfigOption(ConfigOption):
    """App's config option read from config file."""

    def __init__(self, name, value, validator=None, required_in_file=False):
        super().__init__(name, value, validator)
        self.required_in_file = required_in_file


class ArgFileConfigOption(ArgsConfigOption, FileConfigOption):
    """App's config option read both from file and CLI (CLI overrides file)."""

    def __init__(self, name, value, validator, required_in_file, *args,
                 **kwargs):
        ArgsConfigOption.__init__(
                self, name, value, validator, *args, **kwargs)
        self.required_in_file = required_in_file


class PIDFileConfigOption(FileConfigOption):
    """App's config option read from config file specifying PID file path."""

    def __init__(self, value):
        super().__init__('PIDFilePath', value, None, False)


class ParserError(MySCMError):
    pass


def _assert_verbosity_valid(verbosity):
    verb = None
    try:
        verb = int(verbosity)
    except ValueError:
        msg = 'Verbosity specified in configuration file is not integer '\
              '(given value: {})'.format(verbosity)
        raise ParserError(msg)

    if not _MIN_VERBOSITY_LEVEL <= verb <= _MAX_VERBOSITY_LEVEL:
        msg = 'Verbosity must be an integer from range [{}, {}] (given '\
              'value: {})'.format(_MIN_VERBOSITY_LEVEL, _MAX_VERBOSITY_LEVEL,
                                  verb)
        raise ParserError(msg)

    return verb


_DEFAULT_LOG_CONFIG_FILE = '/etc/myscm/log_config.yaml'
_DEFAULT_VERBOSITY_LEVEL = 2
_MIN_VERBOSITY_LEVEL = 0
_MAX_VERBOSITY_LEVEL = 5
_LOG_CONFIG_FILE_VALIDATOR = None

_LOG_CONFIG_FILE_OPTION = FileConfigOption(
        'LogConfigPath',
        _DEFAULT_LOG_CONFIG_FILE,
        _LOG_CONFIG_FILE_VALIDATOR)

_VERBOSITY_OPTION = ArgFileConfigOption(
        'Verbose',
        _DEFAULT_VERBOSITY_LEVEL,
        _assert_verbosity_valid,
        False,
        '-v',
        '--verbose',
        action='count',
        help='increase output and log verbosity')

DEFAULT_CONFIG = [_LOG_CONFIG_FILE_OPTION, _VERBOSITY_OPTION]


class ConfigParser:

    def __init__(self, config_path, config_section_name, default_config,
                 help_desc, version_full):
        self.config = {c.name: None for c in default_config}
        self.allowed_options = {c.name: c for c in default_config}
        self.config_path = config_path
        self.config_section_name = config_section_name
        self.help_desc = help_desc
        self.version_full = version_full

    def _parse(self):
        try:
            self.__parse()
        except (configparser.Error, FileNotFoundError) as e:
            msg = 'Loading server configuration failed'
            raise ParserError(msg, e) from e

    def __parse(self):
        root_parser = self._init_root_parser()
        args, remaining_argv = root_parser.parse_known_args()
        self.config_path = args.conf

        if not os.path.isfile(args.conf):
            msg = "Specified configuration file '{}' doesn't exist".format(
                    args.conf)
            raise ParserError(msg)

        try:
            self._update_config_from_file()
        except ParserError as e:
            msg = "Failed to parse '{}' configuration file".format(
                    self.config_path)
            raise ParserError(msg, e) from e

        try:
            self._update_config_from_argv(root_parser, remaining_argv)
        except ParserError as e:
            msg = 'Failed to parse command line arguments'
            raise ParserError(msg, e) from e

    def _init_root_parser(self):
        # See: http://stackoverflow.com/q/3609852/1321680
        root_parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                add_help=False)
        root_parser.add_argument(
                '-c', '--conf', metavar='FILE', default=self.config_path,
                help='custom configuration file path')
        root_parser.add_argument(
                '--version', action='version', version=self.version_full,
                help='output version information and exit')
        return root_parser

    def _update_config_from_file(self):
        parser = configparser.ConfigParser()
        parser.optionxform = str  # case sensitive
        parser.read(self.config_path)
        file_options = dict(parser.items(self.config_section_name))
        self._assert_no_unrecognized_file_options(file_options)
        self._assert_all_required_options_present(file_options)
        self._convert_string_values_to_types(file_options)
        self._assert_file_options_valid(file_options)
        self.config.update(file_options)

    def _update_config_from_argv(self, root_parser, remaining_argv):
        wrapper_parser = argparse.ArgumentParser(
                parents=[root_parser],
                description=self.help_desc,
                epilog=common.constants.CONFIG_EPILOG,
                formatter_class=SortingHelpFormatter)
        for key, val in self.allowed_options.items():
            if isinstance(val, ArgsConfigOption):
                wrapper_parser.add_argument(*val.args, **val.kwargs)
        wrapper_parser.set_defaults(**self.config)
        argv_options = wrapper_parser.parse_args(remaining_argv)
        self.config.update(vars(argv_options))

    def _convert_string_values_to_types(self, file_options):
        # Without this function, there is a problem with -v option and not only
        for key, val in file_options.items():
            if val.isdigit():
                file_options[key] = int(val)
            elif val in ['true', 'on', 1]:
                file_options[key] = True
            elif val in ['false', 'off', 0]:
                file_options[key] = False
            else:
                file_options[key] = val

    def _assert_no_unrecognized_file_options(self, file_options):
        allowed_keys = set(self.config.keys())
        for key, _ in file_options.items():
            if key not in allowed_keys:
                raise ParserError("Unrecognized option '{}'".format(key))

    def _assert_all_required_options_present(self, file_options):
        file_options_keys = file_options.keys()
        for key, val in self.allowed_options.items():
            if val.required_in_file and key not in file_options_keys:
                msg = "Required option '{}' is not specified in "\
                      "configuration file".format(key)
                raise ParserError(msg)

    def _assert_file_options_valid(self, file_options):
        for key, val in file_options.items():
            self.allowed_options[key].assert_valid(val)


class SortingHelpFormatter(HelpFormatter):
    """Helper class to keep --help options ordered alphabetically."""

    def add_arguments(self, actions):
        actions = sorted(actions, key=attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)
