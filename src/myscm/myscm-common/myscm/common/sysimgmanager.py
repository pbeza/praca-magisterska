# -*- coding: utf-8 -*-
import logging
import os
import re

import termcolor

from myscm.common.error import MySCMError
from myscm.common.signaturemanager import SignatureManager, SignatureManagerError
from myscm.server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SysImgManagerError(MySCMError):
    pass


class SysImgManagerBase:
    """Manager of the system images myscm-img.X.Y.tar.gz (X, Y are integers)
       created by myscm-srv."""

    def __init__(self):
        pass

    def _print_all_verified_img_paths_sorted(self, dir_path, ssl_pub_key_path):
        signature_ext = SignatureManager.SIGNATURE_EXT
        self._print_all_img_paths_sorted(dir_path, True, signature_ext,
                                         ssl_pub_key_path)

    def _print_all_img_paths_sorted(self, dir_path, check_signature=False,
                                    signature_ext=None, ssl_pub_key_path=None):

        paths = self._get_all_img_paths(dir_path)
        n = len(paths)
        paths.sort()

        if paths:
            print("{} mySCM system image{} found in '{}':\n"
                  .format(n, "s" if n > 1 else "", dir_path))
        else:
            print("No mySCM system images found in '{}'.".format(dir_path))

        for fname in paths:
            full_path = os.path.join(dir_path, fname)
            full_path = os.path.realpath(full_path)
            line = "    {}".format(full_path)
            if check_signature:
                signature_info = self._get_signature_info_str(full_path,
                                                              signature_ext,
                                                              ssl_pub_key_path)
                line = "{} [{}]".format(line, signature_info)
            print(line)

    def _color_bold_msg(self, msg, color):
        return termcolor.colored(msg, color, attrs=["bold"])

    def _get_signature_info_str(self, sys_img_path, signature_ext,
                                ssl_pub_key_path):

        sys_img_signature_path = "{}{}".format(sys_img_path, signature_ext)
        info = None
        color = None

        if not os.path.isfile(sys_img_signature_path):
            info = "SSL signature not found"
            color = "grey"
        elif self._verify_sys_img(sys_img_path, sys_img_signature_path,
                                  ssl_pub_key_path):
            info = "SSL signature valid"
            color = "green"
        else:
            info = "SSL signature invalid"
            color = "red"

        return self._color_bold_msg(info, color)

    def _verify_sys_img(self, sys_img_path, sys_img_signature_path,
                        ssl_pub_key_path):
        m = SignatureManager()
        valid = False

        try:
            valid = m.ssl_verify(sys_img_path, sys_img_signature_path,
                                 ssl_pub_key_path)
        except SignatureManagerError as e:
            m = "Failed to verify digital signature '{}'".format(
                    sys_img_signature_path)
            raise SysImgManagerError(m, e) from e

        return valid

    def _get_all_img_paths(self, dir_path):
        """Return list of all found myscm-img.X.Y.tar.gz system images."""

        paths = []
        regex_str = SystemImageGenerator.MYSCM_IMG_FILE_NAME_REGEX
        regex = re.compile(regex_str)
        downloaded_sys_img_dir = os.fsencode(dir_path)

        for f in os.listdir(downloaded_sys_img_dir):
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                paths.append(fname)

        return paths
