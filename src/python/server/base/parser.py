# -*- coding: utf-8 -*-
import common.parser

DEFAULT_CONFIG = []
DEFAULT_CONFIG.extend(common.parser.DEFAULT_CONFIG)


class ConfigParser(common.parser.ConfigParser):

    def __init__(self, config_path, config_section_name, default_config,
                 help_desc, version_full):
        super().__init__(config_path, config_section_name, default_config,
                         help_desc, version_full)


class ServerParserError(common.parser.ParserError):
    pass
