# -*- coding: utf-8 -*-
import os

import common.constants
import server.config
from common.parser import CommandLineFlagConfigOption
from common.parser import ConfigParser
from common.parser import FileConfigOption
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
by the clients using myscm-cli application.'''


class ServerParserError(ParserError):
    pass


class PropagationIntervalGeneralConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI, specifying server's
       propagation interval in seconds."""

    DEFAULT_PROPAGATION_INTERVAL_SEC = 3600

    def __init__(self, propagation_interval_sec=None):
        super().__init__(
            "PropagationIntervalSeconds",
            propagation_interval_sec or self.DEFAULT_PROPAGATION_INTERVAL_SEC,
            self._assert_propagation_interval_valid, False, "-t",
            "--time-prop", metavar="SEC",
            type=self._assert_propagation_interval_valid,
            help="time interval in seconds between sending configuration to "
                 "clients (minimum: {}, maximum: {} seconds, default value: "
                 "{} sec.)".format(_MIN_PROP_INTERVAL_SEC,
                                   _MAX_PROP_INTERVAL_SEC,
                                   self.DEFAULT_PROPAGATION_INTERVAL_SEC))

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
            ssl_cert_path or self.DEFAULT_SSL_CERT_PATH,
            self._assert_ssl_cert_path_valid, True, "--ssl-cert",
            metavar="PATH", type=self._assert_ssl_cert_path_valid,
            help="full path to the server's SSL certificate that is used to "
                 "digitally sign system image generated with --gen-img "
                 "option (default value: '{}')".format(
                    self.DEFAULT_SSL_CERT_PATH))

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
        super().__init__(
            "AIDEConfigPath", aide_config_path or self.DEFAULT_AIDE_CONFIG_PATH,
            self._assert_AIDE_config_path_valid, False, "--aide-conf",
            metavar="PATH", type=self._assert_AIDE_config_path_valid,
            help="AIDE configuration file path that specifies which "
                 "directories of the server system are scanned and "
                 "synchronized with the client's system (default is: '{}')"
                    .format(self.DEFAULT_AIDE_CONFIG_PATH))

    def _assert_AIDE_config_path_valid(self, aide_config_path):
        """AIDE configuration file path option validator."""

        if not os.path.isfile(aide_config_path):
            m = "Given AIDE configuration file '{}' doesn't exist".format(
                    aide_config_path)
            raise ServerParserError(m)

        return aide_config_path


class AIDEScanArgConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI, specifying whether server's scanning
       using AIDE should be ran or not."""

    def __init__(self):
        super().__init__(
            "Scan", "-s", "--scan", action="store_true",
            help="scan system using AIDE, create AIDE's new aide.db reference "
                 "database and rename old one to aide.db.X where X is "
                 "incremented integer")


class ConfigCheckConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI, specifying to check application
       configuration and exit."""

    def __init__(self):
        super().__init__(
                "ConfigCheck", "-k", "--config-check", action="store_true",
                help="check if application configuration is valid and exit; "
                     "0 and 1 indicates respectively: configuration validity "
                     "and invalidity")


class GenerateSystemImageConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from file and/or CLI, specifying whether
       generating system image for the client should be ran or not."""

    def __init__(self):
        super().__init__(
            "GenImg", None, self._assert_client_aide_db_version_valid, "-g",
            "--gen-img", metavar="CLIENT_AIDE_DB_VER",
            type=self._assert_client_aide_db_version_valid,
            help="generate system image that can be applied by any client "
                 "whose system configuration is represented by existing AIDE "
                 "database identified by non-negative integer number "
                 "CLIENT_AIDE_DB_VER (which corresponds to X in aide.db.X "
                 "file created with --scan flag)")

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

        return ver


class SystemImgOutDirConfigOption(FileConfigOption):
    """Configuration option read from file, specifying directory where
       all generated reference system images are saved."""

    DEFAULT_SYS_IMG_DIR = "/var/lib/myscm-srv"

    def __init__(self, sys_img_dir=None):
        super().__init__(
                "SystemImgOutDir",
                sys_img_dir or self.DEFAULT_SYS_IMG_DIR,
                self._assert_sys_img_dir_valid,
                False)

    def _assert_sys_img_dir_valid(self, img_dir_path):
        """Reference system image directory validator."""

        if not os.path.isdir(img_dir_path):
            m = "Value '{}' assigned to variable '{}' doesn't refer to "\
                "directory".format(img_dir_path, self.name)
            raise ServerParserError(m)

        return img_dir_path


class ServerConfigParser(ConfigParser):
    """Application configuration parser for configuration read from both
       configuration file and command line (CLI)."""

    def __init__(self, config_path, config_section_name):
        _SERVER_DEFAULT_CONFIG = [
            PropagationIntervalGeneralConfigOption(),
            SSLCertGeneralConfigOption(),
            AIDEConfigFileGeneralConfigOption(),
            AIDEScanArgConfigOption(),
            ConfigCheckConfigOption(),
            GenerateSystemImageConfigOption(),
            SystemImgOutDirConfigOption()
        ]
        super().__init__(config_path, config_section_name,
                         _SERVER_DEFAULT_CONFIG, _HELP_DESC, _APP_VERSION)

    def parse(self):
        self._parse()
        server_config = server.config.ServerConfig(self.config)
        return server_config
