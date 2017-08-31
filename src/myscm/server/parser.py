# -*- coding: utf-8 -*-
import os

import myscm.common.constants
import myscm.common.parser
import myscm.server.config

from myscm.common.parser import CommandLineFlagConfigOption
from myscm.common.parser import ConfigParser
from myscm.common.parser import GeneralConfigOption
from myscm.common.parser import ParserError
from myscm.common.parser import ValidatedCommandLineConfigOption
from myscm.common.parser import ValidatedFileConfigOption
from myscm.server.aidedbverfile import MySCMDatabaseVersionFile

_APP_VERSION = myscm.common.constants.get_app_version("myscm-srv")
_HELP_DESC = '''This is server side of the mySCM application – simple Software
Configuration Management (SCM) tool for managing software and configuration of
the clients running GNU/Linux distributions. This application is intended to
create and customize GNU/Linux system image that can be applied by the clients
using myscm-cli application.'''


class ServerParserError(ParserError):
    pass


##################################
# Server's configuration options #
##################################


class SSLCertConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI specifying SSL
       certificate file path."""

    DEFAULT_SSL_CERT_PATH = "/etc/myscm-srv/ssl.sig"

    def __init__(self, ssl_cert_path=None):
        super().__init__(
            "SSLCertPath",
            ssl_cert_path or self.DEFAULT_SSL_CERT_PATH,
            self._assert_ssl_cert_path_valid, True, "--ssl-cert",
            metavar="PATH", type=self._assert_ssl_cert_path_valid,
            help="full path to the server's SSL certificate that is being "
                 "used to digitally sign system image generated with "
                 "--gen-img option (default value: '{}')".format(
                    self.DEFAULT_SSL_CERT_PATH))

    def _assert_ssl_cert_path_valid(self, cert_path):
        """SSL certificate path option validator."""

        if not os.path.isfile(cert_path):
            m = "Given SSL certificate file '{}' probably doesn't exist"\
                .format(cert_path)
            raise ServerParserError(m)

        return cert_path


class SSLCertPrivKeyConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI specifying SSL private
       key of the x509 certificate saved in PEM format."""

    DEFAULT_SSL_CERT_PRIV_KEY_PATH = "/etc/myscm-srv/ssl.sig.priv"

    def __init__(self, ssl_priv_key_path=None):
        super().__init__(
            "SSLCertPrivKeyPath",
            ssl_priv_key_path or self.DEFAULT_SSL_CERT_PRIV_KEY_PATH,
            self._assert_ssl_cert_priv_key_path_valid, True, "--ssl-cert-priv",
            metavar="PATH", type=self._assert_ssl_cert_priv_key_path_valid,
            help="full path to the server's SSL private key of the SSL "
                 "certificate saved in PEM format; this key is being used to "
                 "digitally sign system image generated with --gen-img "
                 "option (default value: '{}')".format(
                    self.DEFAULT_SSL_CERT_PRIV_KEY_PATH))

    def _assert_ssl_cert_priv_key_path_valid(self, cert_priv_key_path):
        """SSL private key path option validator."""

        if not os.path.isfile(cert_priv_key_path):
            m = "Given private key path '{}' for SSL certificate file "\
                "probably doesn't exist".format(cert_priv_key_path)
            raise ServerParserError(m)

        return cert_priv_key_path


class AIDEConfigFileConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI specifying AIDE
       configuration file path."""

    DEFAULT_AIDE_CONFIG_PATH = "/etc/myscm-srv/aide.conf"

    def __init__(self, aide_config_path=None):
        super().__init__(
            "AIDEConfigPath", aide_config_path or self.DEFAULT_AIDE_CONFIG_PATH,
            self._assert_AIDE_config_path_valid, False, "-a", "--aide-config",
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
    """Configuration option read from CLI specifying whether server's scanning
       using AIDE should be ran or not."""

    def __init__(self):
        super().__init__(
            "Scan", "-s", "--scan",
            help="scan system using AIDE, create AIDE's new aide.db reference "
                 "database and rename old one to aide.db.X where X is "
                 "incremented integer")


class ListAvailableAIDEDatabasesConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI specifying to list all available
       AIDE databases that describe expected state of the client that want to
       upgrade its configuration."""

    def __init__(self):
        super().__init__(
            "ListDatabases", "--list-db",
            help="list all available AIDE databases created with --scan "
                 "option")


class ListGeneratedMyscmSysImgConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI specifying to list all mySCM system
       images generated with --gen-img option."""

    def __init__(self):
        super().__init__(
            "ListSysImg", "--list-img",
            help="list all mySCM system images created with --gen-img option")


class GenerateSystemImageConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from CLI specifying to generate system image
       from the specified client's cersion to the current newest system
       version. List of all available client's databases can be checked using
       --list-db option."""

    def __init__(self):
        super().__init__(
            "GenImg", None, self._assert_client_aide_db_version_valid, "-g",
            "--gen-img", metavar="SYS_IMG_VER",
            type=self._assert_client_aide_db_version_valid,
            help="generate system image that can be applied by any client "
                 "whose system configuration is represented by existing AIDE "
                 "database identified by non-negative integer number "
                 "SYS_IMG_VER (which corresponds to X in aide.db.X file "
                 "created with --scan flag)")

    def _assert_client_aide_db_version_valid(self, sys_img_ver):
        return myscm.common.parser.assert_sys_img_ver_valid(sys_img_ver)


class SystemImgOutDirConfigOption(ValidatedFileConfigOption):
    """Configuration option read from file specifying directory where
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


class UpgradeConfigOption(ValidatedCommandLineConfigOption):
    """Run --scan and --gen-img option with specified system image version."""

    def __init__(self):
        super().__init__(
            "Upgrade", None, self._assert_client_aide_db_version_valid,
            "--upgrade", metavar="SYS_IMG_VER",
            type=self._assert_client_aide_db_version_valid,
            help="run --scan option and --gen-img option to both scan and "
                 "generate system image")

    def _assert_client_aide_db_version_valid(self, sys_img_ver):
        return myscm.common.parser.assert_sys_img_ver_valid(sys_img_ver)


class RecentlyGeneratedDbVerPathConfigOption(ValidatedFileConfigOption):

    DEFAULT_RECENT_DB_VER_PATH = "/var/myscm-srv/db_ver.myscm-srv"
    OPTION_NAME = "RecentlyGenDbVerPath"

    def __init__(self, recent_db_ver_path=None):
        super().__init__(
            self.OPTION_NAME,
            recent_db_ver_path or self.DEFAULT_RECENT_DB_VER_PATH,
            self._assert_recent_db_ver_path_valid, True)

    def _assert_recent_db_ver_path_valid(self, recent_db_ver_path):
        if not os.path.isfile(recent_db_ver_path):
            m = "Given path '{}' of file holding version of recently "\
                " generated mySCM database file doesn't exist".format(
                    recent_db_ver_path)
            raise ServerParserError(m)

        self._assert_recent_db_ver_file_content_valid(recent_db_ver_path)

        return recent_db_ver_path

    def _assert_recent_db_ver_file_content_valid(self, recent_db_ver_path):
        db_ver_file = MySCMDatabaseVersionFile(recent_db_ver_path)

        try:
            db_ver_file.parse()
        except Exception as e:
            m = "Parsing file '{}' assigned to variable '{}' has failed"\
                .format(recent_db_ver_path, self.OPTION_NAME)
            raise ServerParserError(m, e) from e

        return recent_db_ver_path


#############################################
# Core of the server's configuration parser #
#############################################


class ServerConfigParser(ConfigParser):
    """Application configuration parser for configuration read from both
       configuration file and command line (CLI)."""

    def __init__(self, config_path, config_section_name):
        _SERVER_DEFAULT_CONFIG = [
            SSLCertConfigOption(),
            SSLCertPrivKeyConfigOption(),
            AIDEConfigFileConfigOption(),
            AIDEScanArgConfigOption(),
            ListAvailableAIDEDatabasesConfigOption(),
            ListGeneratedMyscmSysImgConfigOption(),
            GenerateSystemImageConfigOption(),
            SystemImgOutDirConfigOption(),
            UpgradeConfigOption(),
            RecentlyGeneratedDbVerPathConfigOption()
        ]
        super().__init__(config_path, config_section_name,
                         _SERVER_DEFAULT_CONFIG, _HELP_DESC, _APP_VERSION)

    def parse(self):
        self._parse()
        server_config = myscm.server.config.ServerConfig(self.config)
        return server_config
