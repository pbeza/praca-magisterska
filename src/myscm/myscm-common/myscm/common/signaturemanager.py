# -*- coding: utf-8 -*-
import getpass
import logging
import os
import textwrap

import OpenSSL

from myscm.server.error import ServerError

logger = logging.getLogger(__name__)


class SignatureManagerError(ServerError):
    pass


class SignatureManager:
    """Manager of the SSL signatures created to confirm mySCM system images'
       authenticity."""

    SSL_CERT_DIGEST_TYPE = "sha256"
    SIGNATURE_EXT = ".sig"

    def ssl_sign(self, input_path, output_path, priv_key_path):
        priv_key_obj = self._create_priv_key_openssl_obj(input_path,
                                                         priv_key_path)
        if not priv_key_obj:
            return None

        signature = None

        with open(input_path, "rb") as img_f:
            # See: https://stackoverflow.com/q/45141917/1321680
            bytes_to_sign = img_f.read()
            signature = OpenSSL.crypto.sign(priv_key_obj, bytes_to_sign,
                                            self.SSL_CERT_DIGEST_TYPE)

        with open(output_path, "wb") as sig_f:
            sig_f.write(signature)

        # To manually verify validity of the signature run:
        # openssl dgst -sha256 -verify cert_public_key_file.pub -signature cert_file.crt signed_file_path
        # TODO try: gpg --keyserver-options auto-key-retrieve --verify signed_file_path

        return output_path

    def _create_priv_key_openssl_obj(self, input_path, priv_key_path):
        pem_cert_str = self._get_priv_key_str(priv_key_path)
        priv_key = None

        while not priv_key:
            try:
                passwd = self._get_cert_password(input_path, priv_key_path)
            except KeyboardInterrupt as e:
                print()
                logger.info("Generating SSL signature for '{}' skipped by "
                            "user (keyboard interrupt).".format(input_path))
                break

            priv_key = self._get_cert_priv_key(pem_cert_str, passwd)

        return priv_key

    def _get_priv_key_str(self, priv_key_path):
        pem_cert_str = None

        try:
            with open(priv_key_path) as f:
                pem_cert_str = f.read()
        except OSError as e:
            m = "Unable to open '{}' SSL private key for certificate for "\
                "signing system image".format(priv_key_path)
            raise SignatureManagerError(m, e) from e

        return pem_cert_str

    def _get_cert_password(self, input_path, priv_key_path):
        passwd = None

        print()
        m = "Enter password protecting '{}' private key of the SSL "\
            "certificate to digitally sign '{}'. If you want to skip "\
            "generating SSL signature press CTRL+C (or send SIGINT signal in "\
            "any other way).".format(os.path.basename(priv_key_path),
                                     os.path.basename(input_path))
        print(textwrap.fill(m, 80))
        print()

        try:
            passwd = getpass.getpass()
        except getpass.GetPassWarning:
            logger.warning("SSL certificate password input may be echoed!")

        print()

        return passwd

    def _get_cert_priv_key(self, pem_cert_str, passwd):
        CERT_FORMAT_TYPE = OpenSSL.crypto.FILETYPE_PEM
        priv_key = None

        try:
            priv_key = OpenSSL.crypto.load_privatekey(CERT_FORMAT_TYPE,
                                                      pem_cert_str,
                                                      passwd.encode("ascii"))
        except OpenSSL.crypto.Error as e:
            logger.warning("Failed to load SSL certificate private key - "
                           "check if you entered correct password")

        return priv_key

    def ssl_verify(self, path_to_verify, signature_path, ssl_pub_key_path):
        """Return True if SLL signature is valid (otherwise False)."""

        signed_file_data = None
        signature = None
        pem_pkey = None
        SSL_DIGEST_TYPE = self.SSL_CERT_DIGEST_TYPE
        CERT_FORMAT_TYPE = OpenSSL.crypto.FILETYPE_PEM

        with open(path_to_verify, "rb") as f:
            signed_file_data = f.read()

        with open(signature_path, "rb") as f:
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
            raise SignatureManagerError(m, e) from e

        verify_result = None

        try:
            verify_result = OpenSSL.crypto.verify(  # returns None if success
                                    x509_obj, signature, signed_file_data,
                                    SSL_DIGEST_TYPE)
        except OpenSSL.crypto.Error:
            logger.debug("Verification of '{}' signature failed.".format(
                            signature_path))
            verify_result = False
        else:
            verify_result = verify_result is None

        return verify_result
