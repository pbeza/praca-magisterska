# -*- coding: utf-8 -*-
import logging
import os
import paramiko
import pysftp
import random
import re

from myscm.client.error import ClientError
from myscm.client.sysimgmanager import SysImgManager
from myscm.server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SFTPSysImgDownloaderError(ClientError):
    pass


class SFTPSysImgDownloaderNoImageFoundError(SFTPSysImgDownloaderError):
    pass


class SFTPSysImgDownloader:

    DEFAULT_SFTP_PORT = 22

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def download(self):
        try:
            self._sftp_download_myscm_img()
        except SFTPSysImgDownloaderNoImageFoundError as e:
            logger.info(e)

    def _sftp_download_myscm_img(self):
        host = self._get_host()
        port = self.DEFAULT_SFTP_PORT

        try:
            self.__sftp_download_myscm_img(host, port)
        except (paramiko.ssh_exception.AuthenticationException,
                FileNotFoundError) as e:
            m = "Connection to SFTP peer failed"
            raise SFTPSysImgDownloaderError(m, e) from e
        except paramiko.ssh_exception.SSHException as e:
            m = "Connection to SFTP peer failed. Check if '{}' is present in "\
                "SSH known_hosts file".format(host)
            raise SFTPSysImgDownloaderError(m, e) from e

    def __sftp_download_myscm_img(self, host, port):
        user = self.client_config.options.SFTP_username
        passwd = self.client_config.options.SFTP_password  # TODO cert
        download_dir = self.client_config.options.sys_img_download_dir
        remote_dir = "/tmp/myscm"

        logger.debug("Downloading myscm system image from {} (port: {})."
                     .format(host, port))

        # with pysftp.Connection(host, username=user, password=passwd, private_key=..., private_key_pass=...) as sftp:
        with pysftp.Connection(host, username=user, password=passwd) as sftp:
            with sftp.cd(remote_dir):
                img_local_path = self._sftp_get_myscm_img(sftp, download_dir)
                signature_img_path = self._sftp_get_myscm_img_signature(
                                            sftp, download_dir, img_local_path)

        logger.info("mySCM system image successfully downloaded{} from '{}' "
                    "(port: {}, remote file: '{}') and saved in '{}'."
                    .format(" with signature" if signature_img_path else "",
                            host, port,
                            os.path.join(remote_dir, img_local_path),
                            img_local_path))

    def _sftp_get_myscm_img(self, sftp_conn, download_dir):
        img_name = self._get_newest_myscm_sys_img_fname(sftp_conn)
        img_local_path = os.path.join(download_dir, img_name)
        sftp_conn.get(img_name, localpath=img_local_path)

        return img_local_path

    def _sftp_get_myscm_img_signature(self, sftp_conn, download_dir, img_path):
        img_name = os.path.basename(img_path)
        img_sign_name = img_name + SystemImageGenerator.SIGNATURE_EXT
        img_sign_local_path = os.path.join(download_dir, img_sign_name)
        signature_downloaded = False

        if sftp_conn.exists(img_sign_name):
            sftp_conn.get(img_sign_name, localpath=img_sign_local_path)
            signature_downloaded = True
        else:
            logger.warning("Signature file for '{}' doesn't exist.".format(
                           img_path))

        return img_sign_local_path if signature_downloaded else None

    def _get_host(self):
        host = self.client_config.options.update_sys_img

        if isinstance(host, bool):
            if not host:
                m = "IP address option was not specified (internal error)"
                raise SFTPSysImgDownloaderError(m)
            host = random.choice(self.client_config.options.peers_list)
            m = "No host was specified to download myscm image from - "\
                "random host '{}' read from configuration file was selected."\
                .format(host)
            logger.debug(m)

        return host

    def _get_newest_myscm_sys_img_fname(self, sftp_conn):
        img_manager = SysImgManager(self.client_config)
        current_id = img_manager.get_current_system_state_version()
        regex_str = SystemImageGenerator.MYSCM_IMG_FILE_NAME.format(current_id,
                                                                    r"(\d+)")
        regex = re.compile(regex_str)
        max_target_id = -1

        logger.debug("Searching newest myscm image that name matches to '{}' "
                     "regex.".format(regex_str))

        for f in sftp_conn.listdir():
            fname = os.fsdecode(f)
            match = regex.fullmatch(fname)
            if match:
                target_id = int(match.group(1))
                max_target_id = max(target_id, max_target_id)

        if max_target_id < 0:
            m = "No mySCM system images matching current system ID (which is "\
                "{}) found on the connected peer.".format(current_id)
            raise SFTPSysImgDownloaderNoImageFoundError(m)

        newest_img_fname = SystemImageGenerator.MYSCM_IMG_FILE_NAME
        newest_img_fname = newest_img_fname.format(current_id, max_target_id)

        return newest_img_fname
