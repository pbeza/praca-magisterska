# -*- coding: utf-8 -*-
import logging
import logging.config
import yaml

from server.base import baseconfig
from server.multicastserver import parser
import server.multicastserver.constants as srvconstants
import server.multicastserver.error as srverror

config = None
config_parser = None
logger = logging.getLogger(__name__)


class MulticastServerConfig(baseconfig.BaseServerConfig):

    def __init__(self, *options, **kwargs):
        super().__init__(*options, **kwargs)


def init():
    msg = "Loading logging configuration file '{}' failed. "\
          "Details: {}".format("test", "tes")
    config_file_path = srvconstants.CONFIG_FILE_PATH
    config_section_name = srvconstants.CONFIG_SECTION_NAME

    logger.debug('Loading server configuration...')

    _load_server_config(config_file_path, config_section_name)
    _load_logging_config()

    logger.debug('Server configuration successfully loaded')


def __load_server_config(config_file_path, config_section_name):
    global config
    global config_parser
    config_parser = parser.MulticastServerConfigParser(
        config_file_path,
        config_section_name)
    config = config_parser.parse()
    if config.verbose > 1:
        logging.debug('Multicast server configuration:\n{}'.format(
                      vars(config)))


def _load_server_config(config_file_path, config_section_name):
    try:
        __load_server_config(config_file_path, config_section_name)
    except srverror.MulticastServerParserError as e:
        logger.warning(e)


def __load_logging_config():
    global logger
    with open(config.logconfigpath) as f:
        log_config = yaml.load(f)
    logging.config.dictConfig(log_config)
    logger = logging.getLogger(__name__)


def _load_logging_config():
    try:
        __load_logging_config()
    except ValueError as e:
        msg = "Loading logging configuration file '{}' failed. "\
              "Details: {}".format(config.logconfigpath, str(e))
        raise srverror.MulticastServerError(msg, e)
