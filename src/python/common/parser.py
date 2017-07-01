# -*- coding: utf-8 -*-
import argparse
import configparser
import os

from common.error import MySCMError


class ParserError(MySCMError):
    pass


class ConfigOption:
    """Base class for configuration options read from command line (CLI) and/or
       configuration file."""

    def __init__(self, name, value):
        self.name = name
        self.value = value


class ValidatedConfigOption(ConfigOption):
    """Base class for validated key-value configuration option read from
       command line (CLI) and/or configuration file."""

    def __init__(self, name, value, validator):
        super().__init__(name, value)
        self.validator = validator

    def assert_valid(self, value=None):
        if self.validator is not None:
            if value is None:
                value = self.value
            self.validator(value)


class CommandLineConfigOption(ConfigOption):
    """Base class for both command line (CLI) key-value options and boolean
       command line options (a.k.a. 'flags')."""

    def __init__(self, name, value, *args, **kwargs):
        super().__init__(name, value)
        self.args = args
        self.kwargs = kwargs


class ValidatedCommandLineConfigOption(CommandLineConfigOption,
                                       ValidatedConfigOption):
    """Validated key-value configuration option specified as a command line
       (CLI) argument."""

    def __init__(self, name, value, validator, *args, **kwargs):
        ValidatedConfigOption.__init__(self, name, value, validator)
        self.args = args
        self.kwargs = kwargs


class CommandLineFlagConfigOption(CommandLineConfigOption):
    """Boolean configuration option (a.k.a. 'flag') specified as a command line
       (CLI) option."""

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, False)
        self.args = args
        self.kwargs = kwargs


class FileConfigOption(ValidatedConfigOption):
    """Validated key-value configuration option read from application's
       configuration file."""

    def __init__(self, name, value, validator, required_in_file=False):
        super().__init__(name, value, validator)
        self.required_in_file = required_in_file


class GeneralConfigOption(ValidatedCommandLineConfigOption, FileConfigOption):
    """Validated key-value configuration option read from file and/or CLI.
       CLI option overrides respective option read from configuration file."""

    def __init__(self, name, value, validator, required_in_file, *args,
                 **kwargs):
        ValidatedCommandLineConfigOption.__init__(
                self, name, value, validator, *args, **kwargs)
        self.required_in_file = required_in_file
        # Use the same option's name for both config read from CLI and file to
        # allow to override options read from file with options read from CLI.
        self.kwargs.update(dest=name)


class PIDFileConfigOption(FileConfigOption):
    """Configuration option read from config file specifying PID file path."""

    def __init__(self, pid_file_path):
        super().__init__("PIDLockFilePath", pid_file_path,
                         self._assert_pid_path_valid, False)

    def _assert_pid_path_valid(self, pid_file_path):
        """PID file path validator."""

        if os.path.exists(pid_file_path):
            msg = "File path '{}' can't be used for PID lock file - file "\
                  "already exists".format(pid_file_path)
            raise ParserError(msg)

        return pid_file_path


class LogFileConfigOption(FileConfigOption):
    """Config option read from config file specifying log config file path."""

    def __init__(self, log_config_path):
        super().__init__("LogConfigPath", log_config_path,
                         self._assert_log_config_path_valid, False)

    def _assert_log_config_path_valid(self, log_file_path):
        """Log file path validator."""

        if not os.path.isfile(log_file_path):
            msg = "Specified logging configuration '{}' doesn't exist".format(
                    log_file_path)
            raise ParserError(msg)

        return log_file_path


class VerbosityGeneralConfigOption(GeneralConfigOption):
    """Config option read from file and/or CLI specifying logging verbosity."""

    def __init__(self, verbosity_lvl):
        super().__init__("Verbose", verbosity_lvl,
                         self._assert_verbosity_valid,
                         False, "-v", "--verbose", action="count",
                         help="increase output and log verbosity")

    def _assert_verbosity_valid(self, verbosity_string):
        """Verbosity option validator."""

        _MIN_VERBOSITY_LEVEL = 0
        _MAX_VERBOSITY_LEVEL = 5
        verbosity_lvl = None

        try:
            verbosity_lvl = int(verbosity_string)
        except ValueError:
            msg = "Given verbosity is not integer (given value: '{}')"\
                  .format(verbosity_string)
            raise ParserError(msg)

        if not _MIN_VERBOSITY_LEVEL <= verbosity_lvl <= _MAX_VERBOSITY_LEVEL:
            msg = "Verbosity must be an integer from range [{}, {}] (given "\
                  "value: {})".format(_MIN_VERBOSITY_LEVEL,
                                      _MAX_VERBOSITY_LEVEL,
                                      verbosity_lvl)
            raise ParserError(msg)

        return verbosity_lvl


class ConfigParser:
    """Base class for CLI and file based configuration parser."""

    def __init__(self, config_path, config_section_name, default_config,
                 help_desc, version_full):

        self.config_path = config_path
        self.config_section_name = config_section_name
        self.help_desc = help_desc
        self.version_full = version_full

        _COMMON_CONFIG = [
            PIDFileConfigOption("/var/run/lock/myscm-srv.pid"),
            LogFileConfigOption("/etc/myscm/log_config.yaml"),
            VerbosityGeneralConfigOption(2)
        ]
        self.allowed_options = {c.name: c for c in _COMMON_CONFIG}
        self.allowed_options.update({c.name: c for c in default_config})
        self.config = {n: c.value for n, c in self.allowed_options.items()}

    def _parse(self):
        try:
            self.__parse()
        except (configparser.Error, FileNotFoundError) as e:
            msg = "Loading configuration '{}' failed".format(self.config_path)
            raise ParserError(msg, e) from e

    def __parse(self):
        root_parser = self._init_root_parser()
        args, remaining_argv = root_parser.parse_known_args()
        self.config_path = args.config

        # Parsing invalid config file may cause error before printing --help
        if "--help" not in remaining_argv and "-h" not in remaining_argv:
            try:
                self._update_config_from_file()
            except ParserError as e:
                msg = "Failed to parse '{}' configuration file".format(
                        self.config_path)
                raise ParserError(msg, e) from e

        try:
            self._update_config_from_argv(root_parser, remaining_argv)
        except ParserError as e:
            raise ParserError("Failed to parse command line options", e) from e

    def _init_root_parser(self):
        # Options common for all subclasses inheriting from this class
        # See: http://stackoverflow.com/q/3609852/1321680
        root_parser = argparse.ArgumentParser(
                description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                add_help=False)
        root_parser.add_argument(
                "-c", "--config", metavar="FILE", default=self.config_path,
                type=self._assert_conf_file_valid,
                help="read configuration from specified FILE")
        root_parser.add_argument(
                "--version", action="version", version=self.version_full,
                help="output version information and exit", default=False)
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
        project.  To learn more about this implementation, refer to project's
        white paper.'''
        wrapper_parser = argparse.ArgumentParser(
                parents=[root_parser],
                description=self.help_desc,
                epilog=_HELP_EPILOG,
                formatter_class=SortingHelpFormatter)
        for key, val in self.allowed_options.items():
            if isinstance(val, CommandLineConfigOption):
                wrapper_parser.add_argument(*val.args, **val.kwargs)
        wrapper_parser.set_defaults(**self.config)
        try:
            import argcomplete
            argcomplete.autocomplete(wrapper_parser)
        except ImportError:
            pass  # commands autocompletion is not obligatory
        argv_options = wrapper_parser.parse_args(remaining_argv)
        self.config.update(vars(argv_options))

    def _convert_string_values_to_types(self, file_options):
        # Without this function there is problem (among others) with -v option
        for key, val in file_options.items():
            if val.isdigit():
                file_options[key] = int(val)
            elif val in ["true", "on", 1]:
                file_options[key] = True
            elif val in ["false", "off", 0]:
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
            if isinstance(val, FileConfigOption)\
               and val.required_in_file            \
               and key not in file_options_keys:
                msg = "Required option '{}' is not specified in "\
                      "configuration file".format(key)
                raise ParserError(msg)

    def _assert_file_options_valid(self, file_options):
        for key, val in file_options.items():
            self.allowed_options[key].assert_valid(val)


class SortingHelpFormatter(argparse.HelpFormatter):
    """Helper class to keep --help options ordered alphabetically."""

    def add_arguments(self, actions):
        actions.sort(key=_actions_key)
        super(SortingHelpFormatter, self).add_arguments(actions)


def _actions_key(key):
    new_key = key.option_strings[-1]
    if new_key in ["--help", "--version"]:
        return "-Z"  # trick to always display --help and --version last
    return new_key
