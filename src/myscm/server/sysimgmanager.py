# -*- coding: utf-8 -*-
import logging

from myscm.common.sysimgmanager import SysImgManagerBase
from myscm.server.error import ServerError
from myscm.server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SysImgManagerError(ServerError):
    pass


class SysImgManager(SysImgManagerBase):
    """Manager of the system images myscm-img.X.Y.tar.gz (X, Y are integers)
       created by myscm-srv."""

    def __init__(self, server_config):
        super().__init__()
        self.server_config = server_config

    def print_all_verified_img_paths_sorted(self):
        self._print_all_verified_img_paths_sorted(
                        self.server_config.options.system_img_out_dir,
                        SystemImageGenerator.SIGNATURE_EXT,
                        SystemImageGenerator.MYSCM_IMG_FILE_NAME,
                        SystemImageGenerator.SSL_CERT_DIGEST_TYPE,
                        self.server_config.options.SSL_cert_public_key_path)
