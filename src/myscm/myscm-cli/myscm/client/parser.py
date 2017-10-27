# -*- coding: utf-8 -*-
import configparser
import os
import socket

import myscm.client.config
import myscm.common.constants
import myscm.common.parser

from myscm.client.myscmimgverfile import MySCMImgVersionFile
from myscm.client.sysimgupdater import SysImgUpdater
from myscm.common.parser import CommandLineFlagConfigOption
from myscm.common.parser import ConfigParser
from myscm.common.parser import GeneralChoiceConfigOption
from myscm.common.parser import GeneralConfigOption
from myscm.common.parser import ParserError
from myscm.common.parser import ValidatedCommandLineConfigOption
from myscm.common.parser import ValidatedFileConfigOption
from myscm.common.signaturemanager import SignatureManager
from myscm.server.sysimggenerator import SystemImageGenerator

_APP_VERSION = myscm.common.constants.get_app_version("myscm-cli")
_HELP_DESC = '''This is client side of the mySCM application – simple Software
Configuration Management (SCM) tool for managing software and configuration of
the clients running GNU/Linux distributions. This application is intended to
apply GNU/Linux system image created with myscm-srv application.'''


class ClientParserError(ParserError):
    pass


##################################
# Client's configuration options #
##################################


class ApplySysImgConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from CLI specifying to apply changes read
       from given system image (which is tar.gz archive)."""

    def __init__(self):
        super().__init__(
            "ApplyImg", None, self._assert_sys_img_version_valid,
            "--apply-img", metavar="SYS_IMG_VER",
            type=self._assert_sys_img_version_valid,
            help="apply changes to the system updating it to the system state "
                 "identified by unique SYS_IMG_VER integer (which is Y "
                 "integer in {}; X is integer representing current state of "
                 "the system)".format(
                    SystemImageGenerator.MYSCM_IMG_FILE_NAME.format("X", "Y")))

    def _assert_sys_img_version_valid(self, sys_img_ver):
        # After parsing RecentlyAppliedSysImgVerPathConfigOption we need to
        # check if system image myscm-img.X.Y.tar.gz exist (X is recently
        # applied mySCM system image version and Y is sys_img_ver).
        return myscm.common.parser.assert_sys_img_ver_valid(sys_img_ver)


class UpdateSysImgConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from CLI specifying to update system image
       by downloading it from other client or server."""

    def __init__(self, config_path):
        super().__init__(
            "UpdateSysImg", False, self._assert_host_valid, "--update",
            metavar="HOST", type=self._assert_host_valid, nargs="?",
            const=True,
            help="update system image by downloading it from one of the "
                 "clients (chosen randomly) predefined in configuration file "
                 "or by HOST if given; protocol that is used for connection "
                 "is defined by --protocol option or by configuration file if "
                 "--protocol option is not present")
        self.config_path = config_path

    def _assert_host_valid(self, host):
        is_bool_var = isinstance(host, bool)

        if is_bool_var:  # take random if --update HOST not specified
            return host

        valid_host = check_if_host_valid(host)
        self._assert_respective_config_section_exist(host)

        if not valid_host:
            m = "Not valid hostname '{}'".format(host)
            raise ClientParserError(m)

        return host

    def _assert_respective_config_section_exist(self, host):
        # Below parser can be passed as param instead of creating new one
        parser = configparser.ConfigParser()
        parser.optionxform = str  # case sensitive
        parser.read(self.config_path)
        config_sections = parser.sections()

        if host not in config_sections:
            m = "Connection details of the host '{}' are not specified in "\
                "configuration file".format(host)
            raise ClientParserError(m)

        peers_list = parser["myscm-cli"].get("PeersList")

        if host not in peers_list:
            m = "Specified host '{}' needs to be in 'PeersList' "\
                "configuration file list to be able to use it".format(host)
            raise ClientParserError(m)


class UpgradeSysImgConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from CLI specifying to update system image
       by downloading it from other client or server and then to apply
       downloaded system image."""

    def __init__(self):
        super().__init__(
            "UpgradeSysImg", None, self._assert_sys_img_version_valid,
            "--upgrade", metavar="SYS_IMG_VER", nargs="?", const=True,
            type=self._assert_sys_img_version_valid,
            help="equivalent of running --update and --apply-img SYS_IMG_VER "
                 "option; if SYS_IMG_VER is not given, then downloaded mySCM "
                 "will be applied")

    def _assert_sys_img_version_valid(self, sys_img_ver):
        return myscm.common.parser.assert_sys_img_ver_valid(sys_img_ver)


class SSLCertConfigOption(GeneralConfigOption):
    """Configuration option read from file and/or CLI specifying SSL
       certificate file path to verify system image created by myscm-srv."""

    # default if not provided in config file
    DEFAULT_SSL_CERT_PATH = "/etc/ssl/private/myscm-cli.sig"

    def __init__(self, ssl_cert_path=None):
        super().__init__(
            "SSLCertPath",
            ssl_cert_path or self.DEFAULT_SSL_CERT_PATH,
            self._assert_ssl_cert_path_valid, True, "--ssl-cert",
            metavar="PATH", type=self._assert_ssl_cert_path_valid,
            help="full path to the server's SSL certificate that is being "
                 "used to verify signature of the system image generated by "
                 "the myscm-srv (default value: '{}')".format(
                    self.DEFAULT_SSL_CERT_PATH))

    def _assert_ssl_cert_path_valid(self, cert_path):
        """SSL certificate path option validator."""

        if not os.path.isfile(cert_path):
            m = "Given SSL certificate file '{}' probably doesn't exist"\
                .format(cert_path)
            raise ClientParserError(m)

        return cert_path


class UpdateProtocolConfigOption(GeneralChoiceConfigOption):
    """Configuration option read from file and/or CLI specifying which protocol
       should be preferred to download new system image from one of the
       predefined client. This option makes sense only with --update and
       --upgrade options."""

    DEFAULT_PROTOCOL = "SFTP"  # default if not provided in config file

    def __init__(self, protocol=None):
        super().__init__(
            "SysImgUpdateProtocol", protocol or self.DEFAULT_PROTOCOL,
            SysImgUpdater.SUPPORTED_PROTOCOLS, True, "-p", "--protocol",
            metavar="PROTO",
            help="select protocol that will be used to download newest system "
                 "image generated by myscm-srv (default is '{}', allowed "
                 "options are: '{}'); this option makes sense only with "
                 "--update and --upgrade options".format(
                    self.DEFAULT_PROTOCOL,
                    "', '".join(SysImgUpdater.SUPPORTED_PROTOCOLS)))


class PeersListConfigOption(ValidatedFileConfigOption):
    """Configuration option read from file specifying hostnames of the peers
       that share mySCM system images. --update and --upgrade options use this
       list to randomly select client that will be used to download mySCM
       system image (unless host is explicitly specified for those options)."""

    def __init__(self, config_path):
        super().__init__(
            "PeersList", [], self._assert_peers_list_valid, True)
        self.config_path = config_path  # to check referred hostnames' sections

    def _assert_peers_list_valid(self, peers_str):
        peers_str = peers_str.lstrip("[").rstrip("]")
        peers_list = peers_str.split(",") if peers_str else []

        for i in range(len(peers_list)):
            host = peers_list[i].strip()
            valid_host = check_if_host_valid(host)

            if not valid_host:
                m = "One of the hostnames assigned to variable PeersList is "\
                    "not valid (has value: '{}')".format(host)
                raise ClientParserError(m)

            peers_list[i] = host

        return self._peers_list_to_extended_dict(peers_list)

    def _peers_list_to_extended_dict(self, peers_list):
        # Every hostname has its own section, thus need ConfigParser
        # Below parser can be passed as param instead of creating new one
        parser = configparser.ConfigParser()
        parser.optionxform = str  # case sensitive
        parser.read(self.config_path)
        config_sections = parser.sections()

        peers_dict = dict()

        for host in peers_list:
            if host not in config_sections:
                m = "Host '{}' referred in PeersList variable doesn't have "\
                    "respective configuration section with connection details"\
                    .format(host)
                raise ClientParserError(m)

            peers_dict[host] = self._get_host_connection_details(host, parser)

        return peers_dict

    def _get_host_connection_details(self, host, parser):
        host_conn_details = {
            "host": host,
            "protocol": self._get_host_protocol(host, parser),
            "port": self._get_host_port(host, parser),
            "username": self._get_variable_value(host, parser, "Username"),
            "password": self._get_variable_value(
                            host, parser, "Password", required=False),
            "private_key": self._get_variable_fpath(
                            host, parser, "PrivateKey", required=False),
            "private_key_pass": self._get_variable_value(
                            host, parser, "PrivateKeyPasswd", required=False),
            "remote_dir": self._get_variable_value(host, parser, "RemoteDir")
        }

        if not host_conn_details["password"] and\
           not host_conn_details["private_key"]:
            m = "At least one of the 'Password', 'PrivateKey' variables must"\
                "be set in '{}' section".format(host)
            raise ClientParserError(m)

        return host_conn_details

    def _get_host_protocol(self, host, parser):
        protocol = self._get_variable_value(host, parser, "Protocol").upper()

        if protocol not in SysImgUpdater.SUPPORTED_PROTOCOLS:
            m = "Protocol '{}' is not supported".format(protocol)
            raise ClientParserError(m)

        return protocol

    def _get_host_port(self, host, parser):
        MIN_PORT = 1
        MAX_PORT = 65535
        port = self._get_variable_value(host, parser, "Port")
        m = "Value assigned to 'Port' variable needs to be integer from "\
            "range {} - {} (current value: '{}')".format(
                MIN_PORT, MAX_PORT, port)

        try:
            port = int(port)
        except ValueError:
            raise ClientParserError(m)

        if not MIN_PORT <= port <= MAX_PORT:
            raise ClientParserError(m)

        return port

    def _get_variable_fpath(self, host, parser, variable_name, required=True):
        path = self._get_variable_value(host, parser, variable_name, required)

        if not path:
            return path

        if not os.path.isfile(path):
            m = "File path '{}' referred in configuration file section '{}' "\
                "in '{}' variable doesn't exist".format(
                    path, host, variable_name)
            raise ClientParserError(m)

        return path

    def _get_variable_value(self, host, parser, variable_name, required=True):
        value = parser[host].get(variable_name)

        if required and not value:
            m = "Section '{}' doesn't have required '{}' variable"\
                .format(host, variable_name)
            raise ClientParserError(m)

        return value


class VerifySysImgConfigOption(ValidatedCommandLineConfigOption):
    """Configuration option read from CLI specifying to verify signature of
       the given system image."""

    def __init__(self):
        super().__init__(
            "VerifySysImg", None, self._assert_sys_img_to_verify_valid,
            "--verify-img", metavar="PATH",
            type=self._assert_sys_img_to_verify_valid,
            help="verify signature of the given system image")

    def _assert_sys_img_to_verify_valid(self, sys_img_path):
        """System image path option validator."""

        if not os.path.isfile(sys_img_path):
            m = "Given mySCM system image file '{}' probably doesn't exist"\
                .format(sys_img_path)
            raise ClientParserError(m)

        signature_path = sys_img_path + SignatureManager.SIGNATURE_EXT

        if not os.path.isfile(signature_path):
            m = "Given mySCM system image file '{}' doesn't have expected "\
                "corresponding '{}' certificate".format(sys_img_path,
                                                        signature_path)
            raise ClientParserError(m)

        return sys_img_path


class ForceApplyConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI specifying do not bother user with
       interactive questions."""

    def __init__(self):
        super().__init__(
            "ForceApply", "--force",
            help="take default actions and do not ask interactive questions "
                 "while --apply-img")


class ListSysImgConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI specifying to list all available
       system images created by myscm-srv."""

    def __init__(self):
        super().__init__(
            "ListSysImg", "-l", "--list",
            help="list all locally available system images created by "
                 "myscm-srv")


class SysImgExtractDirConfigOption(ValidatedFileConfigOption):

    DEFAULT_SYS_IMG_EXTRACT_DIR = "/tmp"

    def __init__(self, sys_img_extract_dir=None):
        super().__init__(
            "SysImgExtractDir",
            sys_img_extract_dir or self.DEFAULT_SYS_IMG_EXTRACT_DIR,
            self._assert_sys_img_extract_dir_valid, True)

    def _assert_sys_img_extract_dir_valid(self, sys_img_extract_dir):
        if not os.path.isdir(sys_img_extract_dir):
            m = "Value '{}' assigned to variable '{}' doesn't refer to "\
                "directory".format(sys_img_extract_dir, self.name)
            raise ClientParserError(m)

        return sys_img_extract_dir


class SysImgDownloadDirConfigOption(ValidatedFileConfigOption):

    DEFAULT_SYS_IMG_DOWNLOAD_DIR = "/var/lib/myscm-cli/downloaded"

    def __init__(self, sys_img_download_dir=None):
        super().__init__(
            "SysImgDownloadDir",
            sys_img_download_dir or self.DEFAULT_SYS_IMG_DOWNLOAD_DIR,
            self._assert_sys_img_download_dir_valid, True)

    def _assert_sys_img_download_dir_valid(self, sys_img_download_dir):
        if not os.path.isdir(sys_img_download_dir):
            m = "Value '{}' assigned to variable '{}' doesn't refer to "\
                "directory".format(sys_img_download_dir, self.name)
            raise ClientParserError(m)

        return sys_img_download_dir


class RecentlyAppliedSysImgVerPathConfigOption(ValidatedFileConfigOption):

    DEFAULT_RECENT_IMG_VER_PATH = "/var/myscm-cli/img_ver.myscm-cli"
    OPTION_NAME = "RecentSysImgVerPath"

    def __init__(self, recent_img_ver_path=None):
        super().__init__(
            self.OPTION_NAME,
            recent_img_ver_path or self.DEFAULT_RECENT_IMG_VER_PATH,
            self._assert_recent_img_ver_path_valid, True)

    def _assert_recent_img_ver_path_valid(self, recent_img_ver_path):
        if not os.path.isfile(recent_img_ver_path):
            m = "Given path '{}' of file holding version of recently "\
                "applied mySCM system image doesn't exist".format(
                    recent_img_ver_path)
            raise ClientParserError(m)

        img_ver_file = MySCMImgVersionFile(recent_img_ver_path)

        try:
            img_ver_file.parse()
        except Exception as e:
            m = "Parsing file '{}' assigned to variable '{}' has failed".format(
                    recent_img_ver_path, self.OPTION_NAME)
            raise ClientParserError(m, e) from e

        return recent_img_ver_path


class DryRunConfigOption(CommandLineFlagConfigOption):
    """Configuration option read from CLI specifying to not make any real
       changes (--noop or no-operation mode)."""

    def __init__(self):
        super().__init__(
            "DryRun", "--dry-run",
            help="don't make any actions; print which actions would be taken "
                 "if dry run was turned off")


class PrintSysImgVerConfigOption(CommandLineFlagConfigOption):

    def __init__(self):
        super().__init__(
            "PrintSysImgVer", "--print-ver",
            help="print recently applied mySCM system image version (if no "
                 "image was applied yet, then -1 is printed)")


def check_if_host_valid(host):
    is_valid = True

    try:
        socket.getaddrinfo(host, None)
    except:
        is_valid = False

    return is_valid


#############################################
# Core of the client's configuration parser #
#############################################


class ClientConfigParser(ConfigParser):
    """Application configuration parser for configuration read from both
       configuration file and command line (CLI)."""

    def __init__(self, config_path, config_section_name):
        _CLIENT_DEFAULT_CONFIG = [
            ApplySysImgConfigOption(),
            UpdateSysImgConfigOption(config_path),
            UpgradeSysImgConfigOption(),
            SSLCertConfigOption(),
            UpdateProtocolConfigOption(),
            PeersListConfigOption(config_path),
            VerifySysImgConfigOption(),
            ForceApplyConfigOption(),
            ListSysImgConfigOption(),
            SysImgExtractDirConfigOption(),
            SysImgDownloadDirConfigOption(),
            RecentlyAppliedSysImgVerPathConfigOption(),
            DryRunConfigOption(),
            PrintSysImgVerConfigOption()
        ]
        super().__init__(config_path, config_section_name,
                         _CLIENT_DEFAULT_CONFIG, _HELP_DESC, _APP_VERSION)

    def parse(self):
        self._parse()
        client_config = myscm.client.config.ClientConfig(self.config)
        return client_config
