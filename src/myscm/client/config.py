# -*- coding: utf-8 -*-
import logging

from myscm.client.error import ClientError
from myscm.client.myscmimgverfile import MySCMImgVersionFile
from myscm.common.config import BaseConfig

logger = logging.getLogger(__name__)


class ClientConfigError(ClientError):
    pass


class ClientConfig(BaseConfig):
    """Client-specific configuration manager."""

    def __init__(self, *options, **kwargs):
        super().__init__(*options, **kwargs)
        self.img_ver_file = MySCMImgVersionFile(self.options.recent_sys_img_ver_path)
