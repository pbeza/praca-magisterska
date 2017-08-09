# -*- coding: utf-8 -*-
import logging
import os
import re

from myscm.client.error import ClientError
from myscm.client.parser import assert_recent_img_ver_file_content_valid
from myscm.common.sysimgmanager import SysImgManagerBase
from myscm.server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SysImgManagerError(ClientError):
    pass


class SysImgManager(SysImgManagerBase):
    """Manager of the system images myscm-img.X.Y.tar.gz (X, Y are integers)
       created by myscm-srv and downloaded from other client."""

    FIRST_SYS_IMG_VER = 0

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def get_sys_img_path(self):
        current_state_id = self.get_current_system_state_version()
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

    def get_current_system_state_version(self):
        img_ver_path = self.client_config.options.recent_sys_img_ver_path
        ver = None

        if os.path.isfile(img_ver_path):
            ver = self._read_img_ver_from_file(img_ver_path)
        else:
            ver = self._create_new_recent_img_ver_file(img_ver_path)

        return ver

    def update_current_system_state_version(self, sys_img_ver):
        img_ver_path = self.client_config.options.recent_sys_img_ver_path

        if sys_img_ver < 0:
            m = "Updating '{}' file has file since system image version "\
                "can't be less than 0 (is {}).".format(img_ver_path,
                                                       sys_img_ver)
            raise SysImgManagerError(m)

        logger.debug("Updating '{}' file with recently applied system image "
                     "to value {}.".format(img_ver_path, sys_img_ver))

        try:
            with open(img_ver_path, "w") as f:
                f.write(str(sys_img_ver))
        except OSError as e:
            m = "Failed to update '{}' file holding version of the recently "\
                "applied myscm system image".format(img_ver_path)
            raise SysImgManagerError(m, e) from e

    def print_current_system_state_version(self):
        img_ver_path = self.client_config.options.recent_sys_img_ver_path
        ver = -1

        if os.path.isfile(img_ver_path):
            ver = self._read_img_ver_from_file(img_ver_path)

        print(ver)

    def _read_img_ver_from_file(self, img_ver_path):
        ver = assert_recent_img_ver_file_content_valid(img_ver_path)
        logger.debug("Recently applied myscm system image version read from "
                     "'{}': {}.".format(img_ver_path, ver))
        return ver

    def _create_new_recent_img_ver_file(self, img_ver_path):
        logger.debug("'{}' file with recently applied system image doesn't "
                     "exist yet - creating new one".format(
                        img_ver_path))
        try:
            with open(img_ver_path, "w+") as f:
                first_sys_img_ver = self.FIRST_SYS_IMG_VER
                f.write(str(first_sys_img_ver))
        except OSError as e:
            m = "Failed to create new '{}' file holding version of the "\
                "recently applied myscm system image".format(
                    img_ver_path)
            raise SysImgManagerError(m, e) from e

        return self.FIRST_SYS_IMG_VER

    def print_all_verified_img_paths_sorted(self):
        self._print_all_verified_img_paths_sorted(
                        self.client_config.options.sys_img_download_dir,
                        SystemImageGenerator.SIGNATURE_EXT,
                        SystemImageGenerator.MYSCM_IMG_FILE_NAME,
                        SystemImageGenerator.SSL_CERT_DIGEST_TYPE,
                        self.client_config.options.SSL_cert_public_key_path)

    def verify_sys_img(self):
        sys_img_path = self.client_config.options.verify_sys_img
        verification = self._verify_sys_img(
                        sys_img_path,
                        sys_img_path + SystemImageGenerator.SIGNATURE_EXT,
                        self.client_config.options.SSL_cert_public_key_path,
                        SystemImageGenerator.SSL_CERT_DIGEST_TYPE)
        info = "SSL signature {}valid".format("" if verification else "in")
        print(info)

    def get_target_sys_img_ver_from_fname(self, fname):
        regex_str = SystemImageGenerator.MYSCM_IMG_FILE_NAME.format(
                                                            r"(\d+)", r"(\d+)")
        regex = re.compile(regex_str)
        fname = os.path.basename(fname)
        corrupted = False
        m = "Given system image '{}' has unexpected format. MySCM system "\
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
