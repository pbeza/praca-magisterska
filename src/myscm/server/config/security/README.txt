This directory contains files related to security of the system image generated
by the myscm-srv. All system images are singed with x509 certificate using
OpenSSL.

  * request.cnf - Certificate Signing Request (CSR) configuration,
  * request.csr - Certificate Signing Request (CSR) in PEM format,
  * certificate.pem - x509 certificate in PEM format,
  * rsa_aes256_4096.key - encrypted private key in PEM format,
  * rsa_aes256_4096.key.pkcs12 - encrypted private key in PKCS format.
  * rsa_aes256_4096.key.pub - encrypted public key in PEM format,

See also:

  * <https://stackoverflow.com/questions/10782826/digital-signature-for-a-file-using-openssl>
  * https://serverfault.com/questions/9708/what-is-a-pem-file-and-how-does-it-differ-from-other-openssl-generated-key-file
