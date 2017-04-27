#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main starting point for aggregated server application.  Aggregated means
that it consists of 3 types of servers – multicast server, package-proxy server
and log server – which can be ran independently but are aggregated here to
comfortably ran them together on one machine."""

from server.allinoneconfig import AllInOneConfig
from server.allinoneserver import AllInOneServer
from server.base import baseparser
import server.base.constants

logger = logging.getLogger(server.constants.ALL_IN_ONE_SERVER_LOGGER)


def _main(args):
    """Main entry point for the server work."""
    config = AllInOneConfig.from_file(
                             server.multicastserver.constants.CONFIG_FILE_PATH,
                             args)
    logger.info('Starting all-in-one server.')
    server = AllInOneServer(config)
    server.run(config)


def _create_parser():
    parser = argparse.ArgumentParser(
        parents=[baseparser.server_base_parser],
        description='''This is server side of the mySCM application – simple
            Software Configuration Management (SCM) tool for managing clients
            running Debian and Arch Linux based distributions.  This server
            aggregates all, three types of tasks managed by server –
            multicasting configuration, providing package proxy buffer and
            logging clients successes and failures after applying changes by
            them.''')
    return parser


def _print_version():
        print('{} {}'.format(constants.APP_NAME, constants.APP_VERSION))
        print(constants.LICENSE.format(constants.AUTHOR_NAME))
        print()
        print('Written by {} ({})'.format(constants.AUTHOR_NAME,
                                          constants.AUTHOR_EMAIL))


def _test(args):
    from server.multicastserver import multicastserver
    srv = multicastserver.MulticastServer.from_file(
            server.multicastserver.constants.CONFIG_FILE_PATH, args)
    srv.run()


if __name__ == '__main__':
    parser = _create_parser()
    args = parser.parse_args()
    if args.version:
        _print_version()
    else:
        try:
            # _main(args)
            _test(args)
        except FileNotFoundError as e:
            logger.warning(e)
        except Exception as e:
