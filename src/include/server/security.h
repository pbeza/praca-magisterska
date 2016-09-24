/** \file
 * Handling server-specific security issues.
 */
#ifndef _SERVER_SECURITY_H
#define _SERVER_SECURITY_H

#include <openssl/ssl.h>

#include "common/security.h"

/**
 * Default path to file with server's certificate.
 */
#define DEFAULT_CERTIFICATE_PATH	"../config/server/security/certificate.pem"

/**
 * Default path to file with server's private key.
 */
#define DEFAULT_PRIVATE_KEY_PATH	"../config/server/security/rsa_aes256_4096.key"

/**
 * Default password for server's private key unless specified neither in `argv[]`
 * nor in server's configuration file.
 *
 * \warning For safety reasons default password should be unset (set to empty).
 */
#define DEFAULT_PRIVATE_KEY_PASS	{ 0 }

/**
 * Default server's configuration. Options specified in `argv[]` and server's
 * configuration file will overwrite this default configuration.
 */
#define INIT_SECURITY_CONFIG		{\
					.ssl_method = NULL,\
					.ssl_ctx = NULL,\
					.certificate_path = DEFAULT_CERTIFICATE_PATH,\
					.private_key_path = DEFAULT_PRIVATE_KEY_PATH,\
					.private_key_pass = DEFAULT_PRIVATE_KEY_PASS\
					}

#define MAX_PRIV_KEY_PASS_LEN		512

/**
 * Server's OpenSSL configuration common for all threads talking with clients.
 */
typedef struct security_config_t {
	const SSL_METHOD *ssl_method;
	SSL_CTX *ssl_ctx;
	const char *certificate_path; /* TODO TODO TODO */
	const char *private_key_path; /* TODO TODO TODO */
	char private_key_pass[MAX_PRIV_KEY_PASS_LEN];
} security_config_t;

int init_ssl_ctx(security_config_t *security_config);

int accept_client_handshake(SSL *ssl, int socket);

#endif
