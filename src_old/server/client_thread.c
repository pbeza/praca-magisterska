/** \file
 * Implementation of thread dedicated to talk with single client.
 */
#include <fcntl.h>
#include <inttypes.h>
#include <poll.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <syslog.h>
#include <unistd.h>

#include <openssl/ssl.h>

#include "client_thread.h"
#include "packages_manager.h"

#include "common/misc.h"
#include "common/security.h"
#include "common/protocol/proto_failure_packet.h"
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
 * \note \p config_set is treated as a filename of the client's configuration.
 */
static int check_if_config_set_valid(const server_config_t *srv_conf,
				     upgrade_request_t *req) {
	char dir_path[PATH_MAX_LEN];
	char absolute_path[PATH_MAX_LEN];
	uint16_t config_set = req->config_set;

	snprintf(dir_path, ARRAY_LENGTH(dir_path), "%s/%u",
		 srv_conf->configuration_sets_dir,
		 config_set);

	if (!realpath(dir_path, absolute_path)) {
		syslog_errno("realpath() for config set path");
		syslog_errno(dir_path);
		return -1;
	}

	if (check_if_file_exists(absolute_path) < 0) {
		syslog(LOG_ERR, "Requested configuration set '%s' doesn't exit",
		       absolute_path);
		return -1;
	}

	strncpy(req->config_set_absolute_path, absolute_path, strlen(absolute_path));

	return 0;
}

static int check_if_compression_type_valid(compression_type compr_type) {
	return 0 <= compr_type && compr_type < __LAST_COMPRESSION_TYPE_SENTINEL ? 0 : -1;
}

static int check_if_pkg_mgr_valid(package_mgr pkg_mgr) {
	return 0 <= pkg_mgr && pkg_mgr < __LAST_PKG_MGR_TYPE_SENTINEL ? 0 : -1;
}

static int check_if_last_upgrade_time_valid(uint32_t last_upgrade_time) {
	struct timespec spec;

	if (clock_gettime(CLOCK_REALTIME, &spec) < 0) {
		syslog_errno("clock_gettime()");
		return -1;
	}

	return spec.tv_sec < last_upgrade_time ? -1 : 0;
}

static int check_if_upgrade_request_valid(const server_config_t *srv_conf,
					  upgrade_request_t *req,
					  error_code *err_code) {

	if (check_if_config_set_valid(srv_conf, req) < 0) {
		syslog(LOG_ERR, "Received config set number = %" PRIu16
		       " is not valid", req->config_set);
		*err_code = UNKNOWN_CONFIG_SET;
		return -1;
	}

	if (check_if_compression_type_valid(req->compr_type) < 0) {
		syslog(LOG_ERR, "Received compression type = %d is not valid",
		       req->compr_type);
		*err_code = UNKNOWN_COMPR_TYPE;
		return -1;
	}

	if (check_if_pkg_mgr_valid(req->pkg_mgr) < 0) {
		syslog(LOG_ERR, "Received package manager = %d is not valid",
		       req->pkg_mgr);
		*err_code = UNKNOWN_PKG_MGR;
		return -1;
	}

	if (check_if_last_upgrade_time_valid(req->last_upgrade_time) < 0) {
		syslog(LOG_ERR, "Received last upgrade time = %" PRIu32
		       " is not valid because it is in the future");
		return -1;
	}

	return 0;
}

static int prepare_archive_for_client(const server_config_t *srv_conf,
				      const upgrade_request_t *req) {

	/* This operation may take some time... */
	if (download_missing_packages(srv_conf, req) < 0) {
		syslog(LOG_ERR, "Downloading missing packages has failed");
		return -1;
	}

	if (compress_packages(req) < 0) {
		syslog(LOG_ERR, "Compressing packages for client has failed");
		return -1;
	}

	return 0;
}

/**
 * SSL connection is already established successfully. From now on, we need to
 * follow protocol specification to talk with client.
 */
static int start_protocol(const server_config_t *srv_conf, int socket, SSL *ssl) {
	upgrade_request_t req;
	error_code err_code;

	syslog(LOG_DEBUG, "Waiting (polling) for client request %d milliseconds",
	       MSG_POLL_TIMEOUT_MILLISECONDS);

	if (wait_for_client_msg(socket) < 0) {
		syslog(LOG_ERR, "Connection probably lost");
		return -1;
	}

	syslog(LOG_DEBUG, "Reading client's incoming message (UPGRADE_REQUEST"
	       " packet is expected to be received)");

	if (recv_upgrade_request(socket, ssl, &req) < 0) {
		syslog(LOG_ERR, "Failed to receive UPGRADE_REQUEST packet");
		return -1;
	}

	syslog(LOG_DEBUG, "Client's request details: config_set=%" PRIu16
	       ", compr_type=%d, pkg_mgr=%d, last_upgrade_time=%" PRIu32
	       ". Checking whether received request is valid...",
	       req.config_set, req.compr_type, req.pkg_mgr, req.last_upgrade_time);

	if (check_if_upgrade_request_valid(srv_conf, &req, &err_code) < 0) {
		syslog(LOG_ERR, "Received upgrade request is not valid");
		syslog(LOG_DEBUG, "Sending protocol failure packet with "
		       "error code number = %d", err_code);
		if (send_proto_failure(socket, ssl, err_code) < 0)
			syslog(LOG_ERR, "Failed to send protocol failure "
			       "packet after receiving invalid upgrade request");
		return -1;
	}

	if (prepare_archive_for_client(srv_conf, &req) < 0) {
		syslog(LOG_ERR, "Preparing archive for client has failed");
		return -1;
	}

	syslog(LOG_DEBUG, "Sending response to the client (config_set = %"
			PRIu16 ")", req.config_set);

	if (send_response_to_client(socket, ssl) < 0) {
		syslog(LOG_ERR, "Failed to send response to client");
		return -1;
	}

	syslog(LOG_DEBUG, "Response to the client successfully sent");

	return 0;
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
		if (start_protocol(server_config, socket, thread_arg->ssl) < 0)
			syslog(LOG_ERR, "Communication with client has failed");
	}

	if (bidirectional_shutdown_handshake(thread_arg->ssl) < 0)
		syslog(LOG_ERR, "Shutdown handshake has failed");

	SSL_free(thread_arg->ssl);

	return NULL;
}
