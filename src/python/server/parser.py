# -*- coding: utf-8 -*-
import os

import common.constants
import server.config
from common.parser import CommandLineFlagConfigOption
from common.parser import ConfigParser
from common.parser import GeneralConfigOption
from common.parser import ParserError
from common.parser import ValidatedCommandLineConfigOption

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

    DEFAULT_PROPAGATION_INTERVAL_SEC = 3600

    def __init__(self, propagation_interval_sec=None):
        default_val = PropagationIntervalGeneralConfigOption.DEFAULT_PROPAGATION_INTERVAL_SEC
        super().__init__(
            "PropagationIntervalSeconds",
            propagation_interval_sec or default_val,
            self._assert_propagation_interval_valid, False, "-t",
            "--time-prop", metavar="SEC",
            type=self._assert_propagation_interval_valid,
            help="Time interval in seconds between sending configuration to "
                 "clients (minimum {}, maximum {} seconds). Default value: {} "
                 "sec.".format(_MIN_PROP_INTERVAL_SEC,
                               _MAX_PROP_INTERVAL_SEC,
                               default_val))

    def _assert_propagation_interval_valid(self, interval_sec):
        sec = None

        try:
            sec = int(interval_sec)
        except ValueError:
            m = "Specified propagation interval '{}' is not integer from "\
                "range [{}, {}]".format(interval_sec,
                                        _MIN_PROP_INTERVAL_SEC,
                                        _MAX_PROP_INTERVAL_SEC)
            raise ServerParserError(m)

        if not _MIN_PROP_INTERVAL_SEC <= sec <= _MAX_PROP_INTERVAL_SEC:
            m = "Propagation interval must be integer from range [{}, {}] "\
                "(current value: {} sec)".format(
                    _MIN_PROP_INTERVAL_SEC, _MAX_PROP_INTERVAL_SEC, sec)
            raise ServerParserError(m)

        return sec


class SSLCertGeneralConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI, specifying SSL
       certificate file path."""

    DEFAULT_SSL_CERT_PATH = "/etc/myscm-srv/ssl.sig"

    def __init__(self, ssl_cert_path=None):
        super().__init__(
            "SSLCertPath",
            ssl_cert_path or SSLCertGeneralConfigOption.DEFAULT_SSL_CERT_PATH,
            self._assert_ssl_cert_path_valid, True, "--ssl-cert",
            metavar="PATH", type=self._assert_ssl_cert_path_valid,
            help="Full path to the server's SSL certificate that is used to "
                 "digitally sign system image generated with --gen-img "
                 "option. If this option is not present, then default value "
                 "'{}' is used.".format(
                  SSLCertGeneralConfigOption.DEFAULT_SSL_CERT_PATH))

    def _assert_ssl_cert_path_valid(self, cert_path):
        """SSL certificate path option validator."""

        if not os.path.isfile(cert_path):
            m = "Given SSL certificate file '{}' probably doesn't exist"\
                .format(cert_path)
            raise ServerParserError(m)

        return cert_path


class AIDEConfigFileGeneralConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI, specifying AIDE
       configuration file path."""

    DEFAULT_AIDE_CONFIG_PATH = "/etc/myscm-srv/aide.conf"

    def __init__(self, aide_config_path=None):
        default_val = AIDEConfigFileGeneralConfigOption.DEFAULT_AIDE_CONFIG_PATH
        super().__init__(
            "AIDEConfigPath", aide_config_path or default_val,
            self._assert_AIDE_config_path_valid, False, "--aide-conf",
            metavar="PATH", type=self._assert_AIDE_config_path_valid,
            help="AIDE configuration file path. This file specifies which "
                 "directories of the server system are scanned and "
                 "synchronized with the client's system. If not specified "
                 "'{}' file is read by default.".format(default_val))

    def _assert_AIDE_config_path_valid(self, aide_config_path):
        """AIDE configuration file path option validator."""

        if not os.path.isfile(aide_config_path):
            m = "Given AIDE configuration file '{}' doesn't exist".format(
                 aide_config_path)
            raise ServerParserError(m)

        return aide_config_path


class AIDEScanArgConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from file and/or CLI, specifying whether
       server's scanning using AIDE should be ran or not."""

    def __init__(self):
        super().__init__(
            "scan", "-s", "--scan", action="store_true",
            help="Scan system using AIDE, create AIDE's new aide.db reference "
                 "database and rename old one to aide.db.X where X is "
                 "incremented integer. This operation is intended to provide "
                 "AIDE database with a summary of the current state of the "
                 "server machine software without deleting the old state "
                 "file. Scanning may take a long time to complete depending "
                 "on the AIDE configuration file that determines which "
                 "directories are scanned (see --aide-conf option).")


class GenerateSystemImageConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from file and/or CLI, specifying whether
       generating system image for the client should be ran or not."""

    def __init__(self):
        super().__init__(
            "genImg", None, self._assert_client_aide_db_version_valid, "-g",
            "--gen-img", metavar="CLIENT_AIDE_DB_VER",
            help="Generate system image that can be applied by any client "
                 "whose system configuration is represented by existing AIDE "
                 "database identified by non-negative integer number "
                 "CLIENT_AIDE_DB_VER (which corresponds to X in aide.db.X "
                 "file created with --scan flag). Generated system image is "
                 "an archive file saved in location specified in "
                 "configuration file. It contains files necessary to adjust "
                 "client's configuration to match server's configuration. If "
                 "client has never synchronized its configuration with "
                 "server, then 0 should be specified as a CLIENT_AIDE_DB_VER. "
                 "Client application (myscm-cli) has option that prints out "
                 "client's CLIENT_AIDE_DB_VER.")

    def _assert_client_aide_db_version_valid(self, client_aide_db_version):
        ver = None
        valid = True

        try:
            ver = int(client_aide_db_version)
        except ValueError:
            valid = False

        if ver < 0:
            valid = False

        if not valid:
            m = "Specified client's state version '{}' is not non-negative "\
                "integer".format(client_aide_db_version)
            raise ServerParserError(m)

        # TODO check if file exists

        return ver


class ServerConfigParser(ConfigParser):
    """Application configuration parser for configuration read from both
       configuration file and command line (CLI)."""

    def __init__(self, config_path, config_section_name):
        _SERVER_DEFAULT_CONFIG = [
            PropagationIntervalGeneralConfigOption(),
            SSLCertGeneralConfigOption(),
            AIDEConfigFileGeneralConfigOption(),
            AIDEScanArgConfigOption(),
            GenerateSystemImageConfigOption()
        ]
        super().__init__(
            config_path, config_section_name, _SERVER_DEFAULT_CONFIG,
            _HELP_DESC, _APP_VERSION)

    def parse(self):
        self._parse()
        return server.config.ServerConfig(self.config)
