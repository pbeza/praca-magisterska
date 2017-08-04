# -*- coding: utf-8 -*-
import logging
import tarfile

from client.error import ClientError
from client.sysimgmanager import SysImgManager
from client.sysimgvalidator import SysImgValidator

logger = logging.getLogger(__name__)


class SysImgExtractorError(ClientError):
    pass


class SysImgExtractor:

    def __init__(self, client_config):
        self.client_config = client_config
        self.sys_img_manager = SysImgManager(client_config)

    def apply_sys_img(self):
        sys_img_path = self.sys_img_manager.get_sys_img_path()
        extracted_sys_img_dir = None

        try:
            with tarfile.open(sys_img_path) as sys_img_f:
                sys_img_validator = SysImgValidator()
                sys_img_validator.assert_sys_img_valid(sys_img_f)
                extracted_sys_img_dir = self._extract_sys_img(sys_img_f)
            self._apply_added_files(extracted_sys_img_dir)
            self._apply_removed_files(extracted_sys_img_dir)
            self._apply_changed_files(extracted_sys_img_dir)
        except SysImgExtractorError:
            raise
        except Exception as e:
            m = "Failed to apply myscm system image"
            raise SysImgExtractorError(m, e) from e

    def _extract_sys_img(self, sys_img_f):
        return "dir_to_extracted_sys_img"  # TODO TODO TODO

    def _apply_added_files(self, extracted_sys_img_dir):
        pass

    def _apply_removed_files(self, extracted_sys_img_dir):
        pass

    def _apply_changed_files(self, extracted_sys_img_dir):
        pass
