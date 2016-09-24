/** \file
 * Implementation of thread dedicated to talk with single client.
 */
#include <poll.h>
#include <stdlib.h>
#include <syslog.h>
#include <unistd.h>

#include <openssl/ssl.h>

#include "client_thread.h"

#include "common/security.h"

#define MSG_POLL_TIMEOUT_MILLISECONDS	30 * 1000
#define MSGCOUNT			64
#define MAX_SSL_READ_RETRIES		5

static int wait_for_client_msg(int csocket) {
	int is_set;
	struct pollfd fds[] = {
		{ .fd = csocket, .events = POLLIN }
	};

	is_set = TEMP_FAILURE_RETRY(poll(fds, ARRAY_LENGTH(fds),
					 MSG_POLL_TIMEOUT_MILLISECONDS));
	if (is_set < 0) {
		syslog_errno("poll() has failed");
		return -1;
	} else if (!is_set) {
		syslog(LOG_WARNING,
		       "Waiting for client's message has timed out after %dms",
		       MSG_POLL_TIMEOUT_MILLISECONDS);
		return -1;
	}

	return 0;
}

static int read_hello_from_client(SSL *ssl, int socket, char *buf) {
	int ret, retries;

	for (retries = 0; retries < MAX_SSL_READ_RETRIES; retries++) {
		if ((ret = SSL_read(ssl, buf, MSGCOUNT)) > 0) {
			syslog(LOG_DEBUG, "SSL_read() successful, %d bytes read", ret);
			return 0;
		} else if (ret < 0) {
			syslog_ssl_err("SSL_read() = -1, error or action must be taken");
		} else {
			if (SSL_get_error(ssl, ret) == SSL_ERROR_ZERO_RETURN) {
				syslog(LOG_INFO, "Connection was closed "
				       "cleanly during SSL_read()");
				return -1;
			}
			syslog_ssl_err("SSL_read() error, probably connection was closed");
		}

		if ((ret = handle_ssl_error_want(ret, ssl, socket)) < 0) {
			syslog(LOG_ERR, "Trying to handle SSL_read() error has failed");
			return -1;
		}
	}

	if (retries >= MAX_SSL_READ_RETRIES)
		syslog(LOG_ERR, "Maximum number %d of SSL_read() retries "
		       "reached, giving up", MAX_SSL_READ_RETRIES);

	return -1;
}

static void start_protocol(int fd, SSL *ssl) {
	char buf[MSGCOUNT + 1] = { 0 };

	if (wait_for_client_msg(fd) < 0) {
		syslog(LOG_ERR, "Connection probably lost");
		return;
	}

	if (read_hello_from_client(ssl, fd, buf) < 0)
		syslog(LOG_ERR, "Reading hello message from client has failed");
	else
		syslog(LOG_DEBUG, "Incoming msg: '%s'", buf);
}

void* thread_work(thread_arg_t *thread_arg) {
	const server_config_t *server_config = thread_arg->server_config;
	const security_config_t *security_config = SECURITY_CONFIG(server_config);

	int fd = thread_arg->csocket;

	if (init_ssl_conn(security_config->ssl_ctx,
		     &thread_arg->ssl,
		     thread_arg->csocket) < 0) {
		syslog(LOG_ERR, "Initializing SSL thread's connection has failed");
		return NULL;
	}

	if (accept_client_handshake(thread_arg->ssl, thread_arg->csocket) < 0) {
		syslog(LOG_ERR, "Accepting client's handshake has failed");
	} else {
		syslog_ssl_summary(thread_arg->ssl);
		start_protocol(fd, thread_arg->ssl);
	}

	if (bidirectional_shutdown_handshake(thread_arg->ssl) < 0)
		syslog(LOG_ERR, "Shutdown handshake has failed");

	SSL_free(thread_arg->ssl);

	return NULL;
}
