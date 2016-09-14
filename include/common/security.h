/** \file
 * Common for both server and client OpenSSL security implementation.
 */
#ifndef _COMMON_SECURITY_H
#define _COMMON_SECURITY_H

#include <openssl/ssl.h>

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
