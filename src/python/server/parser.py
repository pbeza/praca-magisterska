# -*- coding: utf-8 -*-
import os

import common.constants
import server.config
from common.parser import CommandLineFlagConfigOption
from common.parser import ConfigParser
from common.parser import GeneralConfigOption
from common.parser import ParserError

_MIN_PROP_INTERVAL_SEC = 3
_MAX_PROP_INTERVAL_SEC = 60 * 60 * 24 * 365 * 10
_APP_VERSION = common.constants.get_app_version("myscm-srv")
_HELP_DESC = '''This is server side of the mySCM application – simple
Software Configuration Management (SCM) tool for managing software and
configuration of the clients running GNU/Linux distributions. This application
is intended to create and customize GNU/Linux system image that can be applied
by the client.'''


class ServerParserError(ParserError):
    pass


class PropagationIntervalGeneralConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI, specifying server's
       propagation interval in seconds."""

    def __init__(self, propagation_interval_sec):
        super().__init__(
            "PropagationIntervalSeconds", propagation_interval_sec,
            self._assert_propagation_interval_valid, False, "-t", "--time-prop",
            metavar="SEC", type=self._assert_propagation_interval_valid,
            help="time interval in seconds between sending configuration to "
                 "clients (minimum {}, maximum {} seconds)".format(
                     _MIN_PROP_INTERVAL_SEC, _MAX_PROP_INTERVAL_SEC))

    def _assert_propagation_interval_valid(self, interval_sec):
        sec = None

        try:
            sec = int(interval_sec)
        except ValueError:
            msg = "Specified propagation interval '{}' is not integer from range "\
                  "[{}, {}]".format(interval_sec, _MIN_PROP_INTERVAL_SEC,
                                    _MAX_PROP_INTERVAL_SEC)
            raise ServerParserError(msg)

        if not _MIN_PROP_INTERVAL_SEC <= sec <= _MAX_PROP_INTERVAL_SEC:
            msg = "Propagation interval must be integer from range [{}, {}] "\
                  "(current value: {} sec)".format(
                    _MIN_PROP_INTERVAL_SEC, _MAX_PROP_INTERVAL_SEC, sec)
            raise ServerParserError(msg)

        return sec


class SSLCertGeneralConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI, specifying SSL
       certificate file path."""

    def __init__(self, ssl_cert_path):
        super().__init__(
            "SSLCertPath", ssl_cert_path, self._assert_ssl_cert_path_valid,
            True, "--ssl-cert", metavar="PATH",
            type=self._assert_ssl_cert_path_valid,
            help="file path to server's SSL certificate")

    def _assert_ssl_cert_path_valid(self, cert_path):
        """SSL certificate path option validator."""

        if not os.path.isfile(cert_path):
            msg = "Given certificate file '{}' doesn't exist".format(cert_path)
            raise ServerParserError(msg)

        return cert_path


class AIDEConfigFileGeneralConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI, specifying AIDE
       configuration file path."""

    def __init__(self, aide_config_path):
        super().__init__(
            "AIDEConfigFilePath", aide_config_path,
            self._assert_AIDE_config_path_valid, False, "--aide-conf",
            metavar="PATH", type=self._assert_AIDE_config_path_valid,
            help="AIDE configuration file path")

    def _assert_AIDE_config_path_valid(self, aide_config_path):
        """AIDE configuration file path option validator."""

        if not os.path.isfile(aide_config_path):
            msg = "Given AIDE configuration file '{}' doesn't exist".format(
                    aide_config_path)
            raise ServerParserError(msg)

        return aide_config_path


class AIDEScanArgConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from file and/or CLI, specifying whether
       server's scanning using AIDE should be ran or not."""

    def __init__(self):
        super().__init__(
            "scan", "-s", "--scan", action="store_true",
            help="scans system using AIDE, creates AIDE's new aide.db "
            "reference database and renames old one to database.db.X where X "
            "is incremented integer - this operation may be time consuming "
            "depending on the AIDE configuration that determines which "
            "directories are scanned")


class ServerConfigParser(ConfigParser):
    """Application configuration parser for configuration read from both
       configuration file and command line (CLI)."""

    def __init__(self, config_path, config_section_name):
        _SERVER_DEFAULT_CONFIG = [
            PropagationIntervalGeneralConfigOption(3600),
            SSLCertGeneralConfigOption(None),
            AIDEConfigFileGeneralConfigOption("/etc/myscm-srv/aide.conf"),
            AIDEScanArgConfigOption()
        ]
        super().__init__(
            config_path, config_section_name, _SERVER_DEFAULT_CONFIG,
            _HELP_DESC, _APP_VERSION)

    def parse(self):
        self._parse()
        return server.config.ServerConfig(self.config)
