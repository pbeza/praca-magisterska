# -*- coding: utf-8 -*-
import OpenSSL
import logging
import os
import re

import termcolor

from myscm.common.error import MySCMError
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
        signature_ext = SystemImageGenerator.SIGNATURE_EXT,
        ssl_digest_type = SystemImageGenerator.SSL_CERT_DIGEST_TYPE,

        self._print_all_img_paths_sorted(dir_path, True, signature_ext,
                                         ssl_pub_key_path, ssl_digest_type)

    def _print_all_img_paths_sorted(self, dir_path, check_signature=False,
                                    signature_ext=None, ssl_pub_key_path=None,
                                    ssl_digest_type=None):

        paths = self._get_all_img_paths(dir_path)
        n = len(paths)
        paths.sort()

        if paths:
            print("{} myscm system image{} found in '{}':\n"
                  .format(n, "s" if n > 1 else "", dir_path))
        else:
            print("No myscm system images found in '{}'.".format(dir_path))

        for fname in paths:
            full_path = os.path.join(dir_path, fname)
            full_path = os.path.realpath(full_path)
            line = "    {}".format(full_path)
            if check_signature:
                signature_info = self._get_signature_info_str(full_path,
                                                              signature_ext,
                                                              ssl_pub_key_path,
                                                              ssl_digest_type)
                line = "{} [{}]".format(line, signature_info)
            print(line)

    def _color_bold_msg(self, msg, color):
        return termcolor.colored(msg, color, attrs=["bold"])

    def _get_signature_info_str(self, sys_img_path, signature_ext,
                                ssl_pub_key_path, ssl_digest_type):

        sys_img_signature_path = "{}{}".format(sys_img_path, signature_ext)
        info = None
        color = None

        if not os.path.isfile(sys_img_signature_path):
            info = "SSL signature not found"
            color = "grey"
        elif self._verify_sys_img(sys_img_path, sys_img_signature_path,
                                  ssl_pub_key_path, ssl_digest_type):
            info = "SSL signature valid"
            color = "green"
        else:
            info = "SSL signature invalid"
            color = "red"

        return self._color_bold_msg(info, color)

    def _verify_sys_img(self, sys_img_path, sys_img_signature_path,
                        ssl_pub_key_path, ssl_digest_type):
        """Return True if SLL signature is valid (otherwise False)."""

        signed_file_data = None
        signature = None
        pem_pkey = None
        CERT_FORMAT_TYPE = OpenSSL.crypto.FILETYPE_PEM

        with open(sys_img_path, "rb") as f:
            signed_file_data = f.read()

        with open(sys_img_signature_path, "rb") as f:
            signature = f.read()

        with open(ssl_pub_key_path) as f:
            pem_pkey = f.read()

        # See: https://stackoverflow.com/a/41043382/1321680
        x509_obj = OpenSSL.crypto.X509()

        try:
            pkey = OpenSSL.crypto.load_publickey(CERT_FORMAT_TYPE, pem_pkey)
            x509_obj.set_pubkey(pkey)
        except OpenSSL.crypto.Error as e:
            m = "Loading PEM formatted SSL '{}' certificate's public key "\
                "failed".format(ssl_pub_key_path)
            raise SysImgManagerError(m, e) from e

        verify_result = None

        try:
            verify_result = OpenSSL.crypto.verify(  # returns None if success
                                    x509_obj, signature, signed_file_data,
                                    ssl_digest_type)
        except OpenSSL.crypto.Error as e:
            logger.debug("Verification of '{}' signature failed. Details: "
                         "'{}'.".format(sys_img_signature_path, e))
            verify_result = False
        else:
            verify_result = verify_result is None

        return verify_result

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
