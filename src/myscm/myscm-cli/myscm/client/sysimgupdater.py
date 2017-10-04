# -*- coding: utf-8 -*-
import logging
import random

from myscm.client.error import ClientError
from myscm.client.sftpdownloader import SFTPSysImgDownloader
from myscm.client.sftpdownloader import SFTPSysImgDownloaderError

logger = logging.getLogger(__name__)


class SysImgUpdaterError(ClientError):
    pass


class SysImgDownloaderNoImageFoundError(SysImgUpdaterError):
    pass


class SysImgUpdater:
    """Downloader of the mySCM system images."""

    SUPPORTED_PROTOCOLS_MAPPING = {
        "SFTP": SFTPSysImgDownloader
    }
    SUPPORTED_PROTOCOLS = list(SUPPORTED_PROTOCOLS_MAPPING.keys())

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def update(self):
        host = self.client_config.options.update_sys_img
        img_local_path = None

        if isinstance(host, bool):  # if --update was called without argument
            img_local_path = self._download_from_random_host()
        else:
            img_local_path = self._download_from_selected_host(host)

        return img_local_path

    def _download_from_random_host(self):
        protocol = self.client_config.options.sys_img_update_protocol
        filtered_hosts = self._get_filtered_hosts(protocol)
        downloader = self._get_downloader(protocol)
        filtered_hosts_count = len(filtered_hosts)
        tries = 0
        downloaded = False
        img_local_path = None

        while filtered_hosts and not downloaded:
            tries += 1
            host = random.choice(list(filtered_hosts.keys()))
            host_details = self.client_config.options.peers_list[host]
            n = len(filtered_hosts)
            del filtered_hosts[host]
            m = "No host was explicitly specified to download mySCM image "\
                "from - random host '{}' read from configuration file was "\
                "selected from {} candidate{} (try #{} out of {}).".format(
                    host, n, "s" if n > 1 else "", tries, filtered_hosts_count)
            logger.info(m)

            try:
                img_local_path = downloader.download(host_details)
                downloaded = True
            except SysImgDownloaderNoImageFoundError as e:
                m = "{} Trying out next host.".format(e)
                logger.info(m)
            except SFTPSysImgDownloaderError as e:
                m = "{}. Trying out next host.".format(e)
                logger.warning(m)

        if not downloaded:
            m = "No applicable mySCM system image found ({} host{} checked)."\
                .format(tries, "s" if tries > 1 else "")
            logger.warning(m)

        return img_local_path

    def _get_filtered_hosts(self, protocol):
        all_peers = self.client_config.options.peers_list
        selected_peers_list = {k: v for k, v in all_peers.items() if v["protocol"] == protocol}

        if len(selected_peers_list) == 0:
            m = "No peers were defined with '{}' protocol support".format(
                    protocol)
            raise SysImgUpdaterError(m)

        return selected_peers_list

    def _get_downloader(self, protocol):
        downloader_class = self.SUPPORTED_PROTOCOLS_MAPPING.get(protocol)

        if not downloader_class:
            m = "Protocol '{}' selected in configuration file is not "\
                "supported (allowed protocols: '{}')".format(
                    protocol, "', '".join(self.SUPPORTED_PROTOCOLS))
            raise SysImgUpdaterError(m)

        return downloader_class(self.client_config)

    def _download_from_selected_host(self, host):
        host_details = self.client_config.options.peers_list[host]
        protocol = host_details["protocol"]
        downloader = self._get_downloader(protocol)
        img_local_path = None

        try:
            img_local_path = downloader.download(host_details)
        except SysImgDownloaderNoImageFoundError as e:
            logger.info(e)

        return img_local_path
