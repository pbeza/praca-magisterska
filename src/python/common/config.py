# -*- coding: utf-8 -*-
import logging
import logging.config
import platform
import yaml

from common.error import MySCMError
from common.parser import VerbosityConfigOption

logger = logging.getLogger(__name__)


class ConfigError(MySCMError):
    pass


class BaseConfig:
    """Base class for application configuration."""

    SUPPORTED_LINUX_DISTROS = {"debian", "arch"}

    def __init__(self, *options, **kwargs):
        self.options = ConfigOptions(*options, **kwargs)
        self._load_logging_config(self.options.log_config_path)
        self.distro_name = self._assert_allowed_linux_distro()

    def _load_logging_config(self, log_config_path):
        """Loads YAML configuration file for logging module."""

        try:
            with open(log_config_path) as f:
                log_config = yaml.load(f)
        except (IOError, OSError, yaml.YAMLError) as e:
            m = "Malformed or non-existent logging configuration file '{}'"\
                .format(log_config_path)
            raise ConfigError(m, e) from e

        try:
            logging.config.dictConfig(log_config)
        except ValueError as e:
            m = "Loading logging configuration file '{}' failed".format(
                 log_config_path)
            raise ConfigError(m, e) from e

        base_module = __name__.split(".", 2)[0]
        self.set_log_level(logging.getLogger(base_module))

    def set_log_level(self, logger):
        """Set logging level with respect to loaded configuration."""

        MIN = VerbosityConfigOption.MIN_VERBOSITY_LVL
        LVL_MAPPING = {
            MIN - 3: logging.CRITICAL,  # least verbose level
            MIN - 2: logging.ERROR,
            MIN - 1: logging.WARNING,
            MIN + 0: logging.INFO,      # default logging level
            MIN + 1: logging.DEBUG,
            MIN + 2: logging.NOTSET,    # most verbose level
        }
        LVL = LVL_MAPPING.get(self.options.verbose, logging.NOTSET)
        logger.setLevel(LVL)

    def _assert_allowed_linux_distro(self):
        os_name = platform.system()
        if not os_name:
            os_name = "unknown"

        if os_name.lower() != "linux":
            m = "This software runs on GNU/Linux operating system only ('{}' "\
                "was detected).".format(os_name)
            raise ConfigError(m)

        suffix_msg = "Only Arch and Debian distributions are supported."

        try:
            import distro
        except ImportError:
            m = "Can't check if GNU/Linux is supported! " + suffix_msg
            logger.warning(m)
        else:
            distro_name = distro.id()

            if distro_name not in self.SUPPORTED_LINUX_DISTROS:
                if not distro_name:
                    distro_name = "unknown"
                else:
                    distro_name = "'{}'".format(distro_name)

                logger.warning("Unsupported {} GNU/Linux distribution was "
                               "detected. {}".format(distro_name, suffix_msg))

        return distro_name


class ConfigOptions:
    """Representation of all the options read from configuration file and
       command line (CLI)."""

    def __init__(self, *options, **kwargs):
        """Set attributes from dictionary.
           See: http://stackoverflow.com/q/2466191/1321680"""

        for d in options:
            for key in d:
                new_key = self._camelcase_to_underscore(key)
                setattr(self, new_key, d[key])

        for key in kwargs:
            new_key = self._camelcase_to_underscore(key)
            setattr(self, new_key, kwargs[key])

    def _camelcase_to_underscore(self, key):
        """Converts eg. 'PIDLockFilePath' to 'PID_lock_file_path'."""

        nkey = ""
        n = len(key)

        for i in range(n - 1):
            if key[i].isupper() and key[i + 1].islower():
                nkey += "_" + key[i].lower()
            else:
                nkey += key[i]

        if nkey[0] == "_":
            nkey = nkey[1:]

        return nkey + key[n - 1]
