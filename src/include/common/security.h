/** \file
 * Handling common for both client and server OpenSSL security issues.
 */
#ifndef _COMMON_SECURITY_H
#define _COMMON_SECURITY_H

#include <openssl/ssl.h>

/**
 * Fetch pointer to security configuration from pointer to server's
 * configuration.
 */
#define SECURITY_CONFIG(config)		( &(config)->security_config )

/**
 * This is list of suites that specify algorithms for: encryption,
 * authentication and key exchange. This list includes only suites that provide
 * Perfect Forward Security (PFS), which (for now) are ECDHE (faster) and DHE
 * (slower) cipher suites.
 *
 * \note To allow strong, non-PFS suites, add `HIGH` keyword after `kEDH`. To
 * learn more see:
 * https://www.feistyduck.com/library/openssl-cookbook/online/ch-openssl.html#openssl-cipher-suites-all-together
 * https://vincent.bernat.im/en/blog/2011-ssl-perfect-forward-secrecy.html
 */
#define CIPHER_LIST			"kEECDH+ECDSA kEECDH kEDH +SHA "\
					"!aNULL !eNULL !LOW !3DES !MD5 !EXP "\
					"!DSS !PSK !SRP !kECDH !CAMELLIA "\
					"!IDEA !RC4 !SEED @STRENGTH"

int init_ssl_conn(SSL_CTX *ssl_ctx, SSL **ssl, int csocket);

int bidirectional_shutdown_handshake(SSL *ssl);

/**
 * Send all errors from OpenSSL error buffer to syslog.
 * \todo Check if thread-safe.
 */
void syslog_ssl_err(const char *msg);

int handle_ssl_error_want(int ssl_status, const SSL *ssl, int socket);

void syslog_ssl_summary(const SSL *ssl);

int cleanup_ssl_ctx(SSL_CTX *ssl_ctx);

int ssl_send(int socket, SSL *ssl, const char *buf, size_t len);

int ssl_read(int socket, SSL *ssl, char *buf, int len);

#endif
