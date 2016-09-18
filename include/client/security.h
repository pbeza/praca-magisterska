/** \file
 * Handling client-specific security issues.
 */
#ifndef _CLIENT_SECURITY_H
#define _CLIENT_SECURITY_H

#include <openssl/ssl.h>

#include "common/security.h"

/**
 * Default client's configuration. Options specified in `argv` and server's
 * configuration file will overwrite this default configuration.
 */
#define INIT_SECURITY_CONFIG		{\
					.ssl_method = NULL,\
					.ssl_ctx = NULL,\
					}

/**
 * Client's OpenSSL configuration.
 */
typedef struct security_config_t {
	const SSL_METHOD *ssl_method;
	SSL_CTX *ssl_ctx;
	SSL *ssl;
} security_config_t;

int init_ssl_ctx(security_config_t *config);

int start_ssl_handshake(int socket, SSL *ssl);

#endif
