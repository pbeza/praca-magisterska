#include <openssl/err.h>
#include <openssl/ssl.h>
#include <poll.h>
#include <syslog.h>

#include "common.h"
#include "security.h"

#define SSL_POLL_TIMEOUT_MILLISECONDS	5 * 1000

int init_ssl_conn(SSL_CTX *ssl_ctx, SSL **ssl, int csocket) {
	if (!(*ssl = SSL_new(ssl_ctx))) {
		syslog_ssl_err("SSL_new()");
		return -1;
	}

	if (!(SSL_set_fd(*ssl, csocket))) {
		syslog_ssl_err("SSL_set_fd()");
		SSL_free(*ssl);
		return -1;
	}

	return 0;
}

/**
 * \todo To implement session SSL reusage see `SSL_clear` manual.
 * 'Use the sequence SSL_get_session(3); SSL_new(3); SSL_set_session(3);
 * SSL_free(3) instead to avoid such failures (or simply SSL_free(3);
 * SSL_new(3) if session reuse is not desired).'
 */
int bidirectional_shutdown_handshake(SSL *ssl) {
	/* Send 'close notify' message (see manual) */
	int ret, err;

	ret = SSL_shutdown(ssl);
	err = SSL_get_error(ssl, ret);

	if (!ret && err == SSL_ERROR_SYSCALL) {
		syslog(LOG_DEBUG, "Ignoring SSL_ERROR_SYSCALL after "
		       "SSL_shutdown() returned 0 (see manual for details)");
	} else if (err != SSL_ERROR_NONE) {
		syslog_ssl_err("SSL_get_error() returned error after SSL_shutdown()");
		return -1;
	}

	if (!ret) {
		/* 'close notify' alert was sent, wait for peer's response */
		ret = SSL_shutdown(ssl);
		if (ret != 1) {
			syslog_ssl_err("Receiving 'close notify' via "
				       "SSL_shutdown() has failed");
			err = SSL_get_error(ssl, ret);
			if (err != SSL_ERROR_NONE)
				syslog(LOG_ERR, "SSL_get_error() returned %d", err);
		}
	}

	if (ret == 1)
		syslog(LOG_INFO, "Bidirectional shut down SSL connection success");
	else
		syslog_ssl_err("Bidirectional shut down SSL connection has failed");

	return ret == 1 ? 0 : -1;
}

/**
 * Callback for `ERR_print_errors_cb` function printing OpenSSL error details.
 */
static int syslog_ssl_cb(const char *str, size_t len, void *u) {
	UNUSED(len);
	UNUSED(u);
	syslog(LOG_ERR, "OpenSSL error details: %s", str);
	return 1; /* Undocumented, but 1 must be returned (means success) */
}

void syslog_ssl_err(const char *msg) {
	syslog_errno(msg);
	ERR_print_errors_cb(syslog_ssl_cb, NULL);
}

static int poll_ssl_io(int fd, short events) {
	int status;
	struct pollfd fds[] = {
		{
			.fd = fd,
			.events = events
		}
	};

	syslog(LOG_DEBUG, "SSL_* I/O function returned ERROR_WANT_%s; polling...",
	       events == POLLIN ? "READ" : "WRITE" );

	status = TEMP_FAILURE_RETRY(poll(fds, ARRAY_LENGTH(fds),
					 SSL_POLL_TIMEOUT_MILLISECONDS));
	if (status < 0) {
		syslog_errno("poll() for SSL socket has failed");
		return -1;
	} else if (!status) {
		syslog(LOG_WARNING,
		       "Polling for establishing connection has timed out after %dms",
		       SSL_POLL_TIMEOUT_MILLISECONDS);
		return -1;
	}

	return 0;
}

int handle_ssl_error_want(int ssl_status, const SSL *ssl, int socket) {
	int ret = -1;

	switch (SSL_get_error(ssl, ssl_status)) {
	case SSL_ERROR_WANT_READ:
		if (poll_ssl_io(socket, POLLIN) < 0)
			syslog_ssl_err("ERROR_WANT_READ poll() has failed");
		else
			ret = 0;
		break;
	case SSL_ERROR_WANT_WRITE:
		if (poll_ssl_io(socket, POLLOUT) < 0)
			syslog_ssl_err("ERROR_WANT_WRITE poll() has failed");
		else
			ret = 0;
		break;
	case SSL_ERROR_SYSCALL:
		syslog(LOG_ERR, "SSL_connect() returned SSL_ERROR_SYSCALL");
		break;
	case SSL_ERROR_WANT_CONNECT:
		syslog(LOG_WARNING, "Need to rerun SSL_connect()");
		ret = 0;
		break;
	case SSL_ERROR_WANT_ACCEPT:
		syslog(LOG_WARNING, "Need to rerun SSL_accept()");
		ret = 0;
		break;
	default:
		syslog_ssl_err("Unexpected SSL_connect() error, make sure that "
			       "client uses OpenSSL");
	}

	return ret;
}

void syslog_ssl_summary(const SSL *ssl) {
	syslog(LOG_INFO, "SSL protocol version of a connection: %s,"
	       "SSL cipher name: %s", SSL_get_version(ssl), SSL_get_cipher(ssl));
}
