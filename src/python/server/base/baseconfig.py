# -*- coding: utf-8 -*-
import logging
import yaml

from common.myscmerror import MySCMError


class BaseServerConfig:

    def __init__(self, *options, **kwargs):
        # http://stackoverflow.com/q/2466191/1321680
        for d in options:
            for key in d:
                new_key = self._camelcase_to_underscore(key)
                setattr(self, new_key, d[key])
        for key in kwargs:
            new_key = self._camelcase_to_underscore(key)
            setattr(self, new_key, kwargs[key])

    def _camelcase_to_underscore(self, key):
        # Converts eg. 'PIDFilePath' to 'PID_file_path'
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


def _load_logging_config(logconfigpath):
    try:
        with open(logconfigpath) as f:
            log_config = yaml.load(f)
    except (IOError, OSError, yaml.YAMLError) as e:
        msg = "Malformed or non-existent logging configuration file '{}'"\
                .format(logconfigpath)
        raise MySCMError(msg, e) from e

    try:
        logging.config.dictConfig(log_config)
    except ValueError as e:
        msg = "Loading logging configuration file '{}' failed".format(
              logconfigpath, str(e))
        raise MySCMError(msg, e) from e
