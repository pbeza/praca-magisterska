/** \file
 * Handling server-specific security issues.
 */
#ifndef _SERVER_SECURITY_H
#define _SERVER_SECURITY_H

#include <openssl/ssl.h>

#include "common/security.h"

#include "common/misc.h"

/**
 * Default server's configuration. Options specified in `argv[]` and server's
 * configuration file will overwrite this default configuration.
 */
#define INIT_SECURITY_CONFIG		{\
					.ssl_method = NULL,\
					.ssl_ctx = NULL,\
					.certificate_path = { 0 },\
					.private_key_path = { 0 },\
					.private_key_pass = { 0 }\
					}

/**
 * Maximum allowed length of password protecting server's private key.
 */
#define MAX_PRIV_KEY_PASS_LEN		1024

/**
 * Server's OpenSSL configuration common for all threads talking with clients.
 */
typedef struct security_config_t {
	const SSL_METHOD *ssl_method;
	SSL_CTX *ssl_ctx;
	char certificate_path[PATH_MAX_LEN];
	char private_key_path[PATH_MAX_LEN];
	char private_key_pass[MAX_PRIV_KEY_PASS_LEN];
} security_config_t;

int init_ssl_ctx(security_config_t *security_config);

int accept_client_handshake(SSL *ssl, int socket);

#endif
