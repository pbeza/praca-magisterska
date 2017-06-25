# -*- coding: utf-8 -*-
from argparse import HelpFormatter
import argparse
import configparser
import os

from common.error import MySCMError


class ParserError(MySCMError):
    pass


class ConfigOption:
    """Base class for single validated configuration option."""

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
    """Configuration option specified as a command line (CLI) argument."""

    def __init__(self, name, value, validator, *args, **kwargs):
        super().__init__(name, value, validator)
        self.args = args
        self.kwargs = kwargs
        # Use the same names for both config read from CLI and file to allow to
        # override options read from file with options read from CLI
        self.kwargs.update(dest=name)


class FileConfigOption(ConfigOption):
    """Configuration option read from application's configuration file."""

    def __init__(self, name, value, validator=None, required_in_file=False):
        super().__init__(name, value, validator)
        self.required_in_file = required_in_file


class ArgFileConfigOption(ArgsConfigOption, FileConfigOption):
    """Configuration option read from file and/or CLI (CLI overrides file)."""

    def __init__(self, name, value, validator, required_in_file, *args,
                 **kwargs):
        ArgsConfigOption.__init__(
                self, name, value, validator, *args, **kwargs)
        self.required_in_file = required_in_file


class PIDFileConfigOption(FileConfigOption):
    """Configuration option read from config file specifying PID file path."""

    def __init__(self, pid_file_path):
        super().__init__('PIDLockFilePath', pid_file_path,
                         _assert_pid_path_valid, False)


def _assert_pid_path_valid(pid_file_path):
    """PID file path validator."""

    if os.path.exists(pid_file_path):
        msg = "File path '{}' can't be used for PID file - file already "\
              "exists".format(pid_file_path)
        raise ParserError(msg)

    return pid_file_path


class LogFileConfigOption(FileConfigOption):
    """Config option read from config file specifying log config file path."""

    def __init__(self, log_config_path):
        super().__init__('LogConfigPath', log_config_path, None, False)


class VerbosityArgFileConfigOption(ArgFileConfigOption):
    """Config option read from file and/or CLI specifying app verbosity."""

    def __init__(self, verbosity_lvl):
        super().__init__('Verbose', verbosity_lvl, _assert_verbosity_valid,
                         False, '-v', '--verbose', action='count',
                         help='increase output and log verbosity')


def _assert_verbosity_valid(verbosity_string):
    """Verbosity option validator."""

    _MIN_VERBOSITY_LEVEL = 0
    _MAX_VERBOSITY_LEVEL = 5
    verbosity_lvl = None

    try:
        verbosity_lvl = int(verbosity_string)
    except ValueError:
        msg = 'Given verbosity is not integer (given value: {})'\
              .format(verbosity_string)
        raise ParserError(msg)

    if not _MIN_VERBOSITY_LEVEL <= verbosity_lvl <= _MAX_VERBOSITY_LEVEL:
        msg = 'Verbosity must be an integer from range [{}, {}] (given '\
              'value: {})'.format(_MIN_VERBOSITY_LEVEL, _MAX_VERBOSITY_LEVEL,
                                  verbosity_lvl)
        raise ParserError(msg)

    return verbosity_lvl


class ConfigParser:
    """Base class for CLI and file based configuration parser."""

    def __init__(self, config_path, config_section_name, default_config,
                 help_desc, version_full):
        _COMMON_CONFIG = [
            PIDFileConfigOption('/var/run/lock/myscm-srv.pid'),
            LogFileConfigOption('/etc/myscm/log_config.yaml'),
            VerbosityArgFileConfigOption(2)
        ]
        self.config = {c.name: c.value for c in _COMMON_CONFIG}
        self.config.update({c.name: c.value for c in default_config})
        self.allowed_options = {c.name: c for c in _COMMON_CONFIG}
        self.allowed_options.update({c.name: c for c in default_config})
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
        self.config_path = args.config

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
        # Options common for all subclasses inheriting from this class
        # See: http://stackoverflow.com/q/3609852/1321680
        root_parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                add_help=False)
        root_parser.add_argument(
                '-c', '--config', metavar='FILE', default=self.config_path,
                type=self._assert_conf_file_valid,
                help='custom configuration file path')
        root_parser.add_argument(
                '--version', action='version', version=self.version_full,
                help='output version information and exit', default=False)
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
        # Validity of CLI options is checked by argparse
        self.config.update(file_options)

    def _update_config_from_argv(self, root_parser, remaining_argv):
        _HELP_EPILOG = '''This software is part of the master thesis
        project.  To learn more about this implementation, refer project's
        white paper.'''
        wrapper_parser = argparse.ArgumentParser(
                parents=[root_parser],
                description=self.help_desc,
                epilog=_HELP_EPILOG,
                formatter_class=SortingHelpFormatter)
        for key, val in self.allowed_options.items():
            if isinstance(val, ArgsConfigOption):
                wrapper_parser.add_argument(*val.args, **val.kwargs)
        wrapper_parser.set_defaults(**self.config)
        argv_options = wrapper_parser.parse_args(remaining_argv)
        self.config.update(vars(argv_options))

    def _convert_string_values_to_types(self, file_options):
        # Without this function there is problem (among others) with -v option
        for key, val in file_options.items():
            if val.isdigit():
                file_options[key] = int(val)
            elif val in ['true', 'on', 1]:
                file_options[key] = True
            elif val in ['false', 'off', 0]:
                file_options[key] = False
            else:
                file_options[key] = val

    def _assert_conf_file_valid(self, config_file_path):
        if not os.path.isfile(config_file_path):
            msg = "Specified configuration file '{}' doesn't exist".format(
                    config_file_path)
            raise ParserError(msg)

        return config_file_path

    def _assert_no_unrecognized_file_options(self, file_options):
        allowed_keys = set(self.config.keys())
        for key, _ in file_options.items():
            if key not in allowed_keys:
                raise ParserError("Unrecognized option '{}'".format(key))

    def _assert_all_required_options_present(self, file_options):
        file_options_keys = file_options.keys()
        for key, val in self.allowed_options.items():
            if not isinstance(val, ArgsConfigOption) \
               and val.required_in_file              \
               and key not in file_options_keys:
                msg = "Required option '{}' is not specified in "\
                      "configuration file".format(key)
                raise ParserError(msg)

    def _assert_file_options_valid(self, file_options):
        for key, val in file_options.items():
            self.allowed_options[key].assert_valid(val)


class SortingHelpFormatter(HelpFormatter):
    """Helper class to keep --help options ordered alphabetically."""

    def add_arguments(self, actions):
        actions.sort(key=_actions_key)
        super(SortingHelpFormatter, self).add_arguments(actions)


def _actions_key(key):
    new_key = key.option_strings[-1]
    if new_key in ['--help', '--version']:
        return '-Z'  # trick to always display --help and --version last
    return new_key
