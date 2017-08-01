# -*- coding: utf-8 -*-
import logging

from client.error import ClientError
from common.sysimgmanager import SysImgManagerBase
from server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SysImgManagerError(ClientError):
    pass


class SysImgManager(SysImgManagerBase):
    """Manager of the system images myscm-img.X.Y.tar.gz (X, Y are integers)
       created by myscm-srv and downloaded from other client."""

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def get_newest_available_sys_img_path(self):
        current_state_id = 0  # TODO TODO TODO
        sys_img_ver = self.client_config.options.apply_img

        if current_state_id >= sys_img_ver:
            d = "newer than" if current_state_id > sys_img_ver else "same as"
            m = "Current state of the system (version {}) is {} "\
                "requested version of the system image (version {}) thus no "\
                "need to apply image".format(current_state_id, d, sys_img_ver)
            raise SysImgManagerError(m)

        sys_img_path = None

        try:
            sys_img_path = self._get_sys_img_path(sys_img_ver)
        except Exception as e:
            m = "Failed to get path of the myscm system image for system "\
                "image version {}".format(sys_img_ver)
            raise SysImgManagerError(m, e)

        return sys_img_path

    def _get_newest_available_sys_img_path(self, sys_img_ver):
        # img_name_pattern = SystemImageGenerator.MYSCM_IMG_FILE_NAME
        return None  # TODO TODO TODO

    def print_all_verified_img_paths_sorted(self):
        self._print_all_verified_img_paths_sorted(
                        self.client_config.options.sys_img_download_dir,
                        SystemImageGenerator.SIGNATURE_EXT,
                        SystemImageGenerator.MYSCM_IMG_FILE_NAME,
                        SystemImageGenerator.SSL_CERT_DIGEST_TYPE,
                        self.client_config.options.SSL_cert_public_key_path)
