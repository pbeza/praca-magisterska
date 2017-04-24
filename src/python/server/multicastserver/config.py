# -*- coding: utf-8 -*-
import logging
import logging.config

from server.multicastserver import parser
import server.base.baseconfig as baseconf
import server.multicastserver.constants as srvconstants

config = None
config_parser = None
logger = logging.getLogger(__name__)


class MulticastServerConfig(baseconf.BaseServerConfig):

    def __init__(self, *options, **kwargs):
        super().__init__(*options, **kwargs)


def init():
    _load_server_config(srvconstants.CONFIG_FILE_PATH,
                        srvconstants.CONFIG_SECTION_NAME)
    _load_logging_config()
    logger.info("Server configuration successfully loaded from file '{}' from "
                "section [{}]".format(srvconstants.CONFIG_FILE_PATH,
                                      srvconstants.CONFIG_SECTION_NAME))


def _load_server_config(config_file_path, config_section_name):
    global config
    global config_parser
    config_parser = parser.MulticastServerConfigParser(
            config_file_path,
            config_section_name)
    config = config_parser.parse()
    if config.verbose > 1:
        logger.debug('Successfully loaded multicast server configuration: {}'
                     .format(vars(config)))


def _load_logging_config():
    baseconf._load_logging_config(config.log_config_path)
    global logger
    logger = logging.getLogger(__name__)
