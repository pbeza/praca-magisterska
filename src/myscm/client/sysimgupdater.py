# -*- coding: utf-8 -*-
import logging

from myscm.client.error import ClientError
from myscm.client.sftpdownloader import SFTPSysImgDownloader

logger = logging.getLogger(__name__)


class SysImgUpdaterError(ClientError):
    pass


class SysImgUpdater:
    """Downloader of the MySCM system images."""

    SUPPORTED_PROTOCOLS = {
        "SFTP": SFTPSysImgDownloader
    }

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def update(self):
        selected_protocol = self.client_config.options.sys_img_update_protocol
        downloader_class = self.SUPPORTED_PROTOCOLS.get(selected_protocol)

        if not downloader_class:
            allowed_protocols_str = "', '".join(self.SUPPORTED_PROTOCOLS)
            m = "Protocol '{}' is not supported (allowed protocols: '{}')"\
                .format(selected_protocol, allowed_protocols_str)
            raise SysImgUpdaterError(m)

        downloader_obj = downloader_class(self.client_config)
        downloader_obj.download()
