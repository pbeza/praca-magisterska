### Generating keys ###

[Steps][1] to follow to generate server's:
- private key,
- public key,
- certificate.
For testing purpose use the following password during keys generation:

    minipw

To generate public and private key and save the result in file:

    openssl genrsa -aes256 -out rsa_aes256_4096.key 4096

To check generated keys' details:

    openssl rsa -text -in rsa_aes256_4096.key

### Creating Certificate Signing Requests ###

To generate CSR in interactive mode:

    openssl req -new -key rsa_aes256_4096.key -out request.csr

To verify CSR:

    openssl req -text -in request.csr -noout [-verify]

Instead generating CSR in interactive mode, alternatively use config file:

    openssl req -new -config request.cnf -key fd.key -out request.csr

### Signing certificate ###

To self-sign certificate:

    openssl x509 -req -days 365 -in request.csr -signkey rsa_aes256_4096.key -out certificate.crt

To verify certificate:

    openssl x509 -text -in certificate.crt -noout

### To convert PEM certificate to PKCS12 format for Wireshark ###

Wireshark requires PKCS12 format (not PEM). To convert:

    openssl pkcs12 -export -nocerts -inkey rsa_aes256_4096.key -out /tmp/pkcs12

To display info about PKCS12 file:

    openssl pkcs12 -in /tmp/pkcs12 -info -noout

### Notes ###

BOth certificate and private key is stored in PEM format by default.

For more information and details refer [OpenSSL Cookbook][1].

[1]:https://www.feistyduck.com/library/openssl-cookbook/online/ch-openssl.html
