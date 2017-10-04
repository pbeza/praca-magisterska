# -*- coding: utf-8 -*-
import logging
import os
import re

from myscm.client.error import ClientError
from myscm.common.signaturemanager import SignatureManager, SignatureManagerError
from myscm.common.sysimgmanager import SysImgManagerBase
from myscm.server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SysImgManagerError(ClientError):
    pass


class SysImgManager(SysImgManagerBase):
    """Manager of the myscm-img.X.Y.tar.gz system images (X, Y are integers)
       created by myscm-srv and downloaded from peer."""

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def get_sys_img_path(self):
        current_state_id = self.client_config.img_ver_file.get_version(create=True)
        sys_img_ver = self.client_config.options.apply_img

        if current_state_id >= sys_img_ver:
            d = "newer than" if current_state_id > sys_img_ver else "same as"
            m = "Current state of the system (version {}) is {} and "\
                "requested version of the system image (version {}) thus no "\
                "need to apply image.".format(current_state_id, d, sys_img_ver)
            raise SysImgManagerError(m)

        sys_img_dir = self.client_config.options.sys_img_download_dir
        sys_img_name_pattern = SystemImageGenerator.MYSCM_IMG_FILE_NAME
        sys_img_name = sys_img_name_pattern.format(current_state_id,
                                                   sys_img_ver)
        sys_img_path = os.path.join(sys_img_dir, sys_img_name)

        if not os.path.isfile(sys_img_path):
            m = "'{}' probably doesn't exist. Specify different target "\
                "system image version (specified version: {}).".format(
                    sys_img_path, sys_img_ver)
            raise SysImgManagerError(m)

        return sys_img_path

    def update_current_system_state_version(self, sys_img_ver):
        new_ver = None

        try:
            new_ver = self.client_config.img_ver_file.set_value(sys_img_ver)
        except Exception as e:
            m = "Failed to update '{}' file holding version of the recently "\
                "applied mySCM system image".format(
                    self.client_config.img_ver_file.path)
            raise SysImgManagerError(m, e) from e

        return new_ver

    def print_current_system_state_version(self):
        ver = -1

        if self.client_config.img_ver_file.exist():
            ver = self.client_config.img_ver_file.get_version(create=False)

        print(ver)

    def print_all_verified_img_paths_sorted(self):
        self._print_all_verified_img_paths_sorted(
                        self.client_config.options.sys_img_download_dir,
                        self.client_config.options.SSL_cert_public_key_path)

    def verify_sys_img(self):
        m = SignatureManager()
        sys_img_path = self.client_config.options.verify_sys_img
        signature_path = sys_img_path + SignatureManager.SIGNATURE_EXT
        ssl_pub_key_path = self.client_config.options.SSL_cert_public_key_path
        valid = False

        try:
            valid = m.ssl_verify(sys_img_path, signature_path, ssl_pub_key_path)
        except SignatureManagerError as e:
            m = "Failed to verify '{}' mySCM system image certificate".format(
                    signature_path)
            raise SysImgManagerError(m, e) from e

        info = "SSL signature {}valid".format("" if valid else "in")
        print(info)

    def get_target_sys_img_ver_from_fname(self, fname):
        regex_str = SystemImageGenerator.MYSCM_IMG_FILE_NAME_REGEX
        regex = re.compile(regex_str)
        fname = os.path.basename(fname)
        corrupted = False
        m = "Given system image '{}' has unexpected format. mySCM system "\
            "images need to have '{}' format (X, Y are non negative "\
            "integers).".format(
                fname,
                SystemImageGenerator.MYSCM_IMG_FILE_NAME.format("X", "Y"))
        ver = -1

        match = regex.fullmatch(fname)

        if not match or len(match.groups()) != 2:
            corrupted = True
        else:
            try:
                int(match.group(1))
                ver = int(match.group(2))
            except:
                corrupted = True

        if corrupted:
            raise SysImgManagerError(m)

        return ver
