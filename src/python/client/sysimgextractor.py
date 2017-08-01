# -*- coding: utf-8 -*-
import logging
import tarfile

from client.error import ClientError

logger = logging.getLogger(__name__)


class SysImgExtractorError(ClientError):
    pass


class SysImgExtractor:

    def __init__(self, client_config):
        self.client_config = client_config

    def extract_sys_img(self):
        sys_img_path = # TODO TODO TODO
        pass

    def extract_sys_img_from_path(self, sys_img_path, extract_dir):
        try:
            self._extract_sys_img_from_path(sys_img_path, extract_dir)
        except tarfile.TarError as e:
            m = "Failed to extract '{}' system image".format(sys_img_path)
            raise SysImgExtractorError(m, e) from e

    def _extract_sys_img_from_path(self, sys_img_path, extract_dir):
        with tarfile.open(sys_img_path) as f:
            pass
