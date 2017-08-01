# -*- coding: utf-8 -*-
import argparse
import configparser
import os
import yaml

from common.error import MySCMError


class ParserError(MySCMError):
    pass


###################################################
# Base classes for concrete configuration options #
###################################################


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
        self.kwargs.update(dest=name)


class ValidatedCommandLineConfigOption(ValidatedConfigOption,
                                       CommandLineConfigOption):
    """Validated key-value configuration option specified as a command line
       (CLI) argument."""

    def __init__(self, name, value, validator, *args, **kwargs):
        CommandLineConfigOption.__init__(self, name, value, *args, **kwargs)
        self.validator = validator


class CommandLineFlagConfigOption(CommandLineConfigOption):
    """Boolean configuration option (a.k.a. 'flag') specified as a command line
       (CLI) option."""

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, False, *args, action="store_true", **kwargs)


class FileConfigOption(ConfigOption):
    """Not validated key-value configuration option read from application's
       configuration file."""

    def __init__(self, name, value, required_in_file=False):
        super().__init__(name, value)
        self.required_in_file = required_in_file


class ValidatedFileConfigOption(ValidatedConfigOption, FileConfigOption):
    """Validated key-value configuration option read from application's
       configuration file."""

    def __init__(self, name, value, validator, required_in_file=False):
        FileConfigOption.__init__(self, name, value, required_in_file)
        self.validator = validator


class GeneralConfigOption(ValidatedCommandLineConfigOption,
                          ValidatedFileConfigOption):
    """Validated key-value configuration option read from file and/or CLI.
       CLI option overrides respective option read from configuration file."""

    def __init__(self, name, value, validator, required_in_file, *args,
                 **kwargs):
        ValidatedCommandLineConfigOption.__init__(
                self, name, value, validator, *args, **kwargs)
        self.required_in_file = required_in_file


class GeneralChoiceConfigOption(ValidatedFileConfigOption,
                                CommandLineConfigOption):
    """Key-value configuration option read from file and/or CLI. Option must be
       one of the items from defined set. CLI option overrides respective
       option read from configuration file."""

    def __init__(self, name, value, allowed_values, required_in_file, *args,
                 **kwargs):
        CommandLineConfigOption.__init__(self, name, value, *args,
                                         choices=allowed_values, **kwargs)
        self.required_in_file = required_in_file
        self.validator = self._assert_choices_valid
        self.allowed_values = allowed_values

    def _assert_choices_valid(self, val):
        """Check if given value is from allowed values set."""

        if val not in self.allowed_values:
            m = "'{}' is not acceptabe for '{}' option in configuration "\
                "file. It must be one of the following values: '{}'".format(
                    val, self.name, "', '".join(self.allowed_values))
            raise ParserError(m)

        return val


###############################################################
# Concrete configuration options common for client and server #
###############################################################


class PIDFileConfigOption(ValidatedFileConfigOption):
    """Configuration option read from configuration file specifying full path
       to lock file with process ID (PID)."""

    DEFAULT_LOCK_FILE_PATH = "/var/run/lock/myscm.pid"

    def __init__(self, lock_file_path=None):
        super().__init__(
                "PIDLockFilePath",
                lock_file_path or self.DEFAULT_LOCK_FILE_PATH,
                self._assert_pid_path_valid,
                False)

    def _assert_pid_path_valid(self, pid_file_path):
        """PID file path validator."""

        if os.path.exists(pid_file_path):
            m = "File path '{}' can't be used for PID lock file - file "\
                "already exists".format(pid_file_path)
            raise ParserError(m)

        return pid_file_path


class LogFileConfigOption(ValidatedFileConfigOption):
    """Configuration option read from configuration file specifying full path
       to logging configuration file."""

    DEFAULT_LOG_CONFIG_PATH = "/etc/myscm/log_config.yaml"

    def __init__(self, log_config_path=None):
        super().__init__(
                "LogConfigPath",
                log_config_path or self.DEFAULT_LOG_CONFIG_PATH,
                self._assert_log_config_path_valid,
                False)

    def _assert_log_config_path_valid(self, log_file_path):
        """Log file path validator."""

        if not os.path.isfile(log_file_path):
            m = "Specified logging configuration '{}' doesn't exist".format(
                    log_file_path)
            raise ParserError(m)

        try:
            yaml.load(log_file_path)
        except yaml.YAMLError as e:
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                m = "Invalid logging configuration YAML file '{}'. Error "\
                    "position line: {}, column: {}".format(
                        log_file_path, mark.line + 1, mark.column + 1)
                raise ParserError(m) from e

        return log_file_path


class VerbosityConfigOption(GeneralConfigOption):
    """Configuration option read from configuration file and/or CLI specifying
       application logging verbosity."""

    DEFAULT_VERBOSITY_LVL = 0
    MIN_VERBOSITY_LVL = 0
    MAX_VERBOSITY_LVL = 3

    def __init__(self, verbosity_lvl=None):
        super().__init__(
                "Verbose",
                verbosity_lvl or self.DEFAULT_VERBOSITY_LVL,
                self._assert_verbosity_valid,
                False,
                "-v", "--verbose",
                action="count",
                help="increase output and log verbosity (default "
                     "value: {})".format(self.DEFAULT_VERBOSITY_LVL))

    def _assert_verbosity_valid(self, verbosity_string):
        """Verbosity option validator."""

        lvl = None

        try:
            lvl = int(verbosity_string)
        except ValueError:
            m = "Given verbosity is not integer (given value: '{}')".format(
                    verbosity_string)
            raise ParserError(m)

        if not self.MIN_VERBOSITY_LVL <= lvl <= self.MAX_VERBOSITY_LVL:
            m = "Verbosity must be an integer from range [{}, {}] (given "\
                "value: {})".format(self.MIN_VERBOSITY_LVL,
                                    self.MAX_VERBOSITY_LVL,
                                    lvl)
            raise ParserError(m)

        return lvl


class ConfigCheckConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI specifying to check application
       configuration and exit."""

    def __init__(self):
        super().__init__(
                "ConfigCheck", "-k", "--config-check",
                help="check if application configuration is valid and exit; "
                     "0 and 1 indicates respectively: configuration validity "
                     "and invalidity")


class SSLCertPublicKeyConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI specifying file path of
       the SSL certificate public key to verify system image created with
       --gen-img option."""

    def __init__(self):
        super().__init__(
            "SSLCertPublicKeyPath", None, self._assert_cert_pub_key_path_valid,
            True, "--ssl-pubkey", metavar="PATH",
            type=self._assert_cert_pub_key_path_valid,
            help="full path to the server's public key of the SSL certificate "
                 "that is being used to verify signature of the myscm system "
                 "image generated with the myscm-srv --gen-img option")

    def _assert_cert_pub_key_path_valid(self, cert_pub_key_path):
        """File path to the public key of the SSL certificate validator."""

        if not os.path.isfile(cert_pub_key_path):
            m = "Given SSL certificate public key file '{}' probably doesn't "\
                "exist".format(cert_pub_key_path)
            raise ParserError(m)

        return cert_pub_key_path


#############################################################################
# Options' validators (a.k.a. assertions) common for both server and client #
#############################################################################


def assert_sys_img_ver_valid(sys_img_ver):
    ver = None
    valid = True

    try:
        ver = int(sys_img_ver)
    except ValueError:
        valid = False

    if ver < 0:
        valid = False

    if not valid:
        m = "Specified system image version '{}' cannot be negative integer"\
            .format(sys_img_ver)
        raise ParserError(m)

    return ver


####################################
# Core of the configuration parser #
####################################


class ConfigParser:
    """Base class for CLI and file based configuration parser."""

    _HELP_EPILOG = '''This software is part of the author's master thesis
                      project at the Faculty of Mathematics and Information
                      Science at the Warsaw University of Technology. To learn
                      more about the project refer to project white paper and
                      application manual (`man myscm-srv`).'''

    def __init__(self, config_path, config_section_name, default_config,
                 help_desc, version_full):

        self.config_path = config_path
        self.config_section_name = config_section_name
        self.help_desc = help_desc
        self.version_full = version_full

        _COMMON_CONFIG = [
            PIDFileConfigOption(),
            LogFileConfigOption(),
            VerbosityConfigOption(),
            ConfigCheckConfigOption(),
            SSLCertPublicKeyConfigOption()
        ]

        self.allowed_options = {c.name: c for c in _COMMON_CONFIG}
        self.allowed_options.update({c.name: c for c in default_config})
        self.config = {n: c.value for n, c in self.allowed_options.items()}

    def _parse(self):
        try:
            self.__parse()
        except (configparser.Error, FileNotFoundError) as e:
            m = "Loading configuration '{}' failed".format(self.config_path)
            raise ParserError(m, e) from e

    def __parse(self):
        root_parser = self._init_root_parser()
        wrapper_parser = self._init_wrapper_parser(root_parser)
        args, remaining_argv = root_parser.parse_known_args()
        self.config_path = args.config

        # Parsing invalid config file may cause error before printing --help
        if "--help" not in remaining_argv and "-h" not in remaining_argv:
            try:
                self._update_config_from_file()
            except ParserError as e:
                m = "Failed to parse '{}' configuration file".format(
                        self.config_path)
                raise ParserError(m, e) from e

        try:
            self._update_config_from_argv(root_parser, wrapper_parser,
                                          remaining_argv)
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
                help="read configuration from specified FILE instead of "
                     "default '{}' file".format(self.config_path))
        root_parser.add_argument(
                "--version", action="version", version=self.version_full,
                help="output version information and exit", default=False)
        return root_parser

    def _init_wrapper_parser(self, root_parser):
        wrapper_parser = argparse.ArgumentParser(
                parents=[root_parser],
                description=self.help_desc,
                epilog=self._HELP_EPILOG,
                formatter_class=SortingHelpFormatter)
        for key, val in self.allowed_options.items():
            if isinstance(val, CommandLineConfigOption):
                wrapper_parser.add_argument(*val.args, **val.kwargs)
        try:
            import argcomplete
            argcomplete.autocomplete(wrapper_parser)
        except ImportError:
            pass  # commands autocompletion is not obligatory

        return wrapper_parser

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

    def _update_config_from_argv(self, root_parser, wrapper_parser,
                                 remaining_argv):
        wrapper_parser.set_defaults(**self.config)
        argv_options = wrapper_parser.parse_args(remaining_argv)
        # Validity of CLI options is assured by argparse
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
            m = "Specified configuration file '{}' doesn't exist".format(
                    config_file_path)
            raise ParserError(m)

        return config_file_path

    def _assert_no_unrecognized_file_options(self, file_options):
        allowed_keys = set(self.config.keys())
        for key, _ in file_options.items():
            if key not in allowed_keys:
                raise ParserError("Unrecognized option '{}'".format(key))

    def _assert_all_required_options_present(self, file_options):
        for key, val in self.allowed_options.items():
            if isinstance(val, FileConfigOption)\
               and val.required_in_file         \
               and key not in file_options.keys():
                m = "Required option '{}' is not specified in "\
                    "configuration file".format(key)
                raise ParserError(m)

    def _assert_file_options_valid(self, file_options):
        for key, val in file_options.items():
            option = self.allowed_options[key]
            if isinstance(option, ValidatedConfigOption):
                option.assert_valid(val)


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
