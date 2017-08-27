### Generating keys ###

[Steps][1] to follow to generate server's:

  - private key,
  - public key,
  - certificate.

For testing purpose use the following password during keys generation:

    minipw

To generate public and private key and save the result in a file run:

    openssl genrsa -aes256 -out certificate.key 4096

To check generated keys' details run:

    openssl rsa -text -in certificate.key


### Creating Certificate Signing Requests ###

To generate CSR in interactive mode run:

    openssl req -new -key certificate.key -out request.csr

To verify CSR run:

    openssl req -text -in request.csr -noout [-verify]

Instead generating CSR in interactive mode, alternatively use config file:

    openssl req -new -config request.cnf -key fd.key -out request.csr


### Signing certificate ###

To self-sign certificate run:

    openssl x509 -req -days 365 -in request.csr -signkey certificate.key -out certificate.pem

To verify certificate run:

    openssl x509 -text -in certificate.pem -noout
    openssl verify -verbose certificate.pem


### To convert PEM certificate to PKCS12 format (e.g. for Wireshark) ###

Wireshark requires PKCS12 format (not PEM). To convert run:

    openssl pkcs12 -export -nocerts -inkey certificate.key -out /tmp/pkcs12

To display info about PKCS12 file run:

    openssl pkcs12 -in /tmp/pkcs12 -info -noout


### Notes ###

Both certificate and private key is stored in PEM format by default.

For more information and details refer [OpenSSL Cookbook][1].


[1]:https://www.feistyduck.com/library/openssl-cookbook/online/ch-openssl.html
