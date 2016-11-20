/** \file
 * Implementation of thread dedicated to talk with single client.
 */
#include <fcntl.h>
#include <inttypes.h>
#include <poll.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <syslog.h>
#include <unistd.h>

#include <openssl/ssl.h>

#include "client_thread.h"

#include "common/security.h"
#include "protocol/proto_upgrade_response.h"
#include "protocol/recv_upgrade_request.h"

#define MSG_POLL_TIMEOUT_MILLISECONDS	30 * 1000
#define ARCHIVES_DIR_PATH		"/tmp/"
#define ARCHIVE_FILENAME		"test.txt"
#define ARCHIVE_FULL_PATH		ARCHIVES_DIR_PATH ARCHIVE_FILENAME

/**
 * After successful SSL handshake client should send first request (with respect
 * to the protocol specification) within \a MSG_POLL_TIMEOUT_MILLISECONDS
 * milliseconds. This function waits this period of time by polling.
 */
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

static int send_response_to_client(int socket, SSL *ssl) {
	int fd;
	struct stat st;
	const char *fpath = ARCHIVE_FULL_PATH;

	if (stat(fpath, &st) < 0) {
		syslog(LOG_ERR, "Failed to stat() '%s' file to get file's size",
		       fpath);
		return -1;
	}

	if ((fd = TEMP_FAILURE_RETRY(open(fpath, O_RDONLY))) < 0) {
		syslog(LOG_ERR, "Failed to open %s", fpath);
		return -1;
	}

	if (send_upgrade_response(socket, ssl, st.st_size, fd) < 0) {
		syslog(LOG_ERR, "Failed to send response to client");
		return -1;
	}

	if (TEMP_FAILURE_RETRY(close(fd)) < 0) {
		syslog_errno("Failed to close() file");
		return -1;
	}

	return 0;
}

/**
 * SSL connection is already established successfully. From now on, we need to
 * follow protocol specification to talk with client.
 */
static void start_protocol(int socket, SSL *ssl) {
	upgrade_request_t upgrade_request;

	syslog(LOG_DEBUG, "Waiting (polling) for client request %d milliseconds",
	       MSG_POLL_TIMEOUT_MILLISECONDS);

	if (wait_for_client_msg(socket) < 0) {
		syslog(LOG_ERR, "Connection probably lost");
		return;
	}

	syslog(LOG_DEBUG, "Reading client's incoming message");

	if (recv_upgrade_request(socket, ssl, &upgrade_request) < 0) {
		syslog(LOG_ERR, "Failed to receive UPGRADE_REQUEST packet");
		return;
	}

	syslog(LOG_DEBUG, "Client's request details: config_set=%" PRIu16
	       ", compr_type=%d, pkg_mgr=%d, last_upgrade_time=%" PRIu32,
	       upgrade_request.config_set, upgrade_request.compr_type,
	       upgrade_request.pkg_mgr, upgrade_request.last_upgrade_time);

	syslog(LOG_DEBUG, "Sending response to the client");

	if (send_response_to_client(socket, ssl) < 0) {
		syslog(LOG_ERR, "Failed to send response to client");
		return;
	}

	syslog(LOG_DEBUG, "Response to the client successfully sent");
}

void* thread_work(thread_arg_t *thread_arg) {
	const server_config_t *server_config = thread_arg->server_config;
	const security_config_t *security_config = SECURITY_CONFIG(server_config);
	int socket = thread_arg->csocket;

	if (init_ssl_conn(security_config->ssl_ctx, &thread_arg->ssl,
			  thread_arg->csocket) < 0) {
		syslog(LOG_ERR, "Initializing SSL thread's connection has failed");
		return NULL;
	}

	if (accept_client_handshake(thread_arg->ssl, thread_arg->csocket) < 0) {
		syslog(LOG_ERR, "Accepting client's SSL handshake has failed");
	} else {
		syslog(LOG_INFO, "Accepting client's SSL handshake successful");
		syslog_ssl_summary(thread_arg->ssl);
		start_protocol(socket, thread_arg->ssl);
	}

	if (bidirectional_shutdown_handshake(thread_arg->ssl) < 0)
		syslog(LOG_ERR, "Shutdown handshake has failed");

	SSL_free(thread_arg->ssl);

	return NULL;
}
