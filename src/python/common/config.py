# -*- coding: utf-8 -*-
import logging
import logging.config
import yaml

from common.error import MySCMError


class ConfigError(MySCMError):
    pass


class BaseConfig:
    """Base class for application configuration."""

    def __init__(self, *options, **kwargs):
        self.options = ConfigOptions(*options, **kwargs)
        self._load_logging_config(self.options.log_config_path)

    def _load_logging_config(self, log_config_path):
        """Loads YAML configuration file for logging module."""

        try:
            with open(log_config_path) as f:
                log_config = yaml.load(f)
        except (IOError, OSError, yaml.YAMLError) as e:
            msg = "Malformed or non-existent logging configuration file '{}'"\
                    .format(log_config_path)
            raise ConfigError(msg, e) from e

        try:
            logging.config.dictConfig(log_config)
        except ValueError as e:
            msg = "Loading logging configuration file '{}' failed".format(
                  log_config_path)
            raise ConfigError(msg, e) from e


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

        nkey = ''
        n = len(key)

        for i in range(n - 1):
            if key[i].isupper() and key[i + 1].islower():
                nkey += '_' + key[i].lower()
            else:
                nkey += key[i]

        if nkey[0] == '_':
            nkey = nkey[1:]

        return nkey + key[n - 1]
