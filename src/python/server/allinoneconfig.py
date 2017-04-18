# -*- coding: utf-8 -*-
from server.multicastserver import config as mcastconf


class AllInOneConfig:
    """Configuration of all the server's modules."""

    def __init__(self, multicast_server_config, pkg_proxy_server_config,
                 log_server_config):
        self.multicast_server_config = multicast_server_config
        self.pkg_proxy_server_config = pkg_proxy_server_config
        self.log_server_config = log_server_config

    @classmethod
    def from_file(cls, config_path, args=None):
        mcast_srv_config = mcastconf.MulticastServerConfig(config_path)
        pkg_srv_config = None  # TODO
        log_srv_config = None  # TODO
        return AllInOneConfig(mcast_srv_config, pkg_srv_config, log_srv_config)
