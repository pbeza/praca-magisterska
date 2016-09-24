/** \file
 * Handling client-specific security issues.
 */
#ifndef _CLIENT_SECURITY_H
#define _CLIENT_SECURITY_H

#include <openssl/ssl.h>

#include "common/security.h"

#include "common/misc.h"

/**
 * Default path to server's trusted certificate in PEM format.
 */
#ifdef DEBUG
#define DEFAULT_TRUSTED_CERT_PATH	"../config/server/security/certificate.pem"
#else
#define DEFAULT_TRUSTED_CERT_PATH	"/etc/" MAIN_PROJECT_NAME "/" PROJECT_NAME "/trusted_certificate.pem"
#endif

#define DEFAULT_TRUSTED_CERT_PATH_DIR	"/etc/ssl/certs"

/**
 * Default client's configuration. Options specified in `argv[]` and server's
 * configuration file will overwrite this default configuration.
 */
#define INIT_SECURITY_CONFIG		{\
					.ssl_method = NULL,\
					.ssl_ctx = NULL,\
					.ssl = NULL,\
					.trusted_cert_file = DEFAULT_TRUSTED_CERT_PATH,\
					.trusted_cert_dir = DEFAULT_TRUSTED_CERT_PATH_DIR\
					}

/**
 * Client's OpenSSL configuration.
 */
typedef struct security_config_t {
	/**
	 * Connection method used during SSL session.
	 */
	const SSL_METHOD *ssl_method;
	/**
	 * SSL configuration context. Base for per-connection SSL configuration.
	 */
	SSL_CTX *ssl_ctx;
	/**
	 * Per-connection SSL configuration created from context configuration.
	 */
	SSL *ssl;
	/**
	 * Path to server's trusted certificate in PEM format.
	 */
	char trusted_cert_file[PATH_MAX_LEN];
	/**
	 * Path to directory with certificates in PEM format.
	 */
	char trusted_cert_dir[PATH_MAX_LEN];
} security_config_t;

int init_ssl_ctx(security_config_t *config);

int start_ssl_handshake(int socket, SSL *ssl);

#endif
