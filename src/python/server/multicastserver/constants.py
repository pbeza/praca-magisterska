# -*- coding: utf-8 -*-
import common.constants

APP_NAME = 'myscm-multicast-srv'
APP_VERSION = '0.1'
CONFIG_FILE_PATH = 'server/config/config.ini'
CONFIG_SECTION_NAME = 'multicastserver'
CONF_VAR_PROPAGATION_INTERVAL = 'PropagationIntervalSeconds'

DEFAULT_CONFIG = {
    CONF_VAR_PROPAGATION_INTERVAL: 3600,
    common.constants.CONF_VAR_PID_FILE_PATH: '/var/run/myscm-multicast-srv.pid'
}
DEFAULT_CONFIG.update(common.constants.DEFAULT_CONFIG)
