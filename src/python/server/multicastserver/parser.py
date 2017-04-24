# -*- coding: utf-8 -*-
import os

from server.multicastserver import config
import common.constants
import common.parser
import server.base.parser
import server.multicastserver.constants


def _assert_propagation_interval_valid(interval_sec):
    sec = None
    try:
        sec = int(interval_sec)
    except ValueError:
        msg = "Specified propagation interval '{}' is not integer from range "\
              "[{}, {}]".format(sec,
                                _MIN_PROP_INTERVAL_SEC,
                                _MAX_PROP_INTERVAL_SEC)
        raise MulticastServerParserError(msg)

    if not _MIN_PROP_INTERVAL_SEC <= sec <= _MAX_PROP_INTERVAL_SEC:
        msg = 'Propagation interval must be integer from range [{}, {}] '\
              '(current value: {}sec)'.format(_MIN_PROP_INTERVAL_SEC,
                                              _MAX_PROP_INTERVAL_SEC,
                                              sec)
        raise MulticastServerParserError(msg)

    return sec


def _assert_ssl_cert_path_valid(cert_path):
    if not os.path.isfile(cert_path):
        msg = "Certificate '{}' specified in configuration file doesn't exist"\
                .format(cert_path)
        raise MulticastServerParserError(msg)

    return cert_path


_MIN_PROP_INTERVAL_SEC = 3
_MAX_PROP_INTERVAL_SEC = 100000000
_HELP_DESC = '''This is multicast server side of the mySCM application – simple
Software Configuration Management (SCM) tool for managing clients running
Debian and Arch Linux based distributions.  This server is intended to send
configuration to all of the clients using Pragmatic General Multicast (PGM)
protocol.'''
_DEFAULT_PROPAGATION_INTERVAL_SEC = 3600
_DEFAULT_PID_FILE_PATH = '/var/run/lock/myscm-multicast-srv.pid'

_PROPAGATION_INTERVAL_OPTION = common.parser.ArgFileConfigOption(
        'PropagationIntervalSeconds', _DEFAULT_PROPAGATION_INTERVAL_SEC,
        _assert_propagation_interval_valid, False, '-t', '--time-prop',
        metavar='SEC', type=_assert_propagation_interval_valid,
        help='time interval in seconds between sending configuration to '
             'clients (minimum {}, maximum {} seconds)'.format(
                 _MIN_PROP_INTERVAL_SEC,
                 _MAX_PROP_INTERVAL_SEC))
_PID_FILE_OPTION = common.parser.PIDFileConfigOption(_DEFAULT_PID_FILE_PATH)
_SSL_CERT_FILE_OPTION = common.parser.ArgFileConfigOption(
        'SSLCertPath', None, None, True, '--cert', metavar='PATH',
        type=_assert_ssl_cert_path_valid,
        help="file path to server's SSL certificate")
_DEFAULT_CONFIG = [
        _PROPAGATION_INTERVAL_OPTION, _PID_FILE_OPTION, _SSL_CERT_FILE_OPTION]
_DEFAULT_CONFIG.extend(server.base.parser.DEFAULT_CONFIG)


class MulticastServerConfigParser(server.base.parser.ConfigParser):

    def __init__(self, config_path, config_section_name):
        super(MulticastServerConfigParser, self).__init__(
                config_path, config_section_name, _DEFAULT_CONFIG, _HELP_DESC,
                server.multicastserver.constants.APP_VERSION_LONG)

    def parse(self):
        self._parse()
        return config.MulticastServerConfig(self.config)


class MulticastServerParserError(server.base.parser.ServerParserError):
    pass
