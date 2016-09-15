/** \file
 * Common for both server and client OpenSSL security implementation.
 */
#ifndef _COMMON_SECURITY_H
#define _COMMON_SECURITY_H

#include <openssl/ssl.h>

/**
 * This is list of suites that specify algorithms for: encryption,
 * authentication and key exchange. This list include only suites that provide
 * Perfect Forward Security (PFS).
 *
 * \note To allow strong, non-PFS suites, add `HIGH` keyword after `kEDH`. To
 * learn more see:
 * https://www.feistyduck.com/library/openssl-cookbook/online/ch-openssl.html#openssl-cipher-suites-all-together
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

#endif
