# -*- coding: utf-8 -*-
import logging
import os
import paramiko
import pysftp
import re

from myscm.client.error import ClientError
from myscm.server.sysimggenerator import SystemImageGenerator

logger = logging.getLogger(__name__)


class SFTPSysImgDownloaderError(ClientError):
    pass


class SFTPSysImgDownloader:

    def __init__(self, client_config):
        super().__init__()
        self.client_config = client_config

    def download(self, host_details):
        self._sftp_download_myscm_img(host_details)

    def _sftp_download_myscm_img(self, host_details):
        try:
            self.__sftp_download_myscm_img(host_details)
        except (paramiko.ssh_exception.AuthenticationException,
                FileNotFoundError) as e:
            m = "Connection to SFTP peer failed"
            raise SFTPSysImgDownloaderError(m, e) from e
        except paramiko.ssh_exception.SSHException as e:
            m = "Connection to SFTP peer failed. Check if '{}' is present in "\
                "SSH known_hosts file. If you are using private key to "\
                "connect to the server, check if password provided in "\
                "configuration file is correct".format(host_details["host"])
            raise SFTPSysImgDownloaderError(m, e) from e

    def __sftp_download_myscm_img(self, host_details):
        protocol = host_details["protocol"]
        host = host_details["host"]
        port = host_details["port"]
        username = host_details["username"]
        password = host_details["password"]
        private_key = host_details["private_key"]
        private_key_pass = host_details["private_key_pass"]
        remote_dir = host_details["remote_dir"]

        conn_details = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "private_key": private_key,
            "private_key_pass": private_key_pass,
        }
        download_dir = self.client_config.options.sys_img_download_dir

        logger.info("Downloading mySCM system image from {} (port: {}) "
                    "using {} protocol.".format(host, port, protocol))

        if private_key:  # prefer public key authentication over password
            del conn_details["password"]
        else:
            del conn_details["private_key"]
            del conn_details["private_key_pass"]

        # Quite ugly hotfix for bug in pysftp module that leads to printing
        # module's ignored internal exception when e.g. SFTP credentials are
        # incorrect.

        _tmp_del = pysftp.Connection.__del__
        pysftp.Connection.__del__ = lambda x: None  # in case of failure

        with pysftp.Connection(**conn_details) as sftp:
            # Revert hotfix is success
            pysftp.Connection.__del__ = _tmp_del
            sftp.__del__ = _tmp_del

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

    def _get_newest_myscm_sys_img_fname(self, sftp_conn):
        current_id = self.client_config.img_ver_file.get_version(create=False)
        regex_str = SystemImageGenerator.MYSCM_IMG_FILE_NAME.format(current_id,
                                                                    r"(\d+)")
        regex = re.compile(regex_str)
        max_target_id = -1

        logger.debug("Searching newest mySCM image that name matches to '{}' "
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
            from myscm.client.sysimgupdater import SysImgDownloaderNoImageFoundError
            raise SysImgDownloaderNoImageFoundError(m)

        newest_img_fname = SystemImageGenerator.MYSCM_IMG_FILE_NAME
        newest_img_fname = newest_img_fname.format(current_id, max_target_id)

        return newest_img_fname
