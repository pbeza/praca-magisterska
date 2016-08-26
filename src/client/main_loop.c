#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <poll.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "common/network.h"
#include "main_loop.h"

#define POLL_TIMEOUT_MILLISECONDS	10 * 1000

/**
 * If `connect` function was interrupted by `EINTR`, connection is established
 * asynchronously. This function handles this case.
 */
static int poll_for_asynchronous_connection(int fd) {
	int is_set, status;
	socklen_t size = sizeof(int);
	struct pollfd fds[1] = { 0 };
	fds[0].fd = fd;
	fds[0].events = POLLIN;
	is_set = TEMP_FAILURE_RETRY(poll(fds, ARRAY_LENGTH(fds), POLL_TIMEOUT_MILLISECONDS));
	if (is_set < 0) {
		ERR("poll");
	} else if (!is_set) {
		syslog(LOG_WARNING,
		       "Polling for establishing connection has timed out after %dms",
		       POLL_TIMEOUT_MILLISECONDS);
		return -1;
	} else {
		if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &status, &size) < 0)
			ERR("getsockopt");
		if (status) {
			syslog(LOG_ERR, "getsockopt reports failure");
			return -1;
		}
	}
	return 0;
}

int connect_server(const client_config_t *config) {
	const struct sockaddr_in *addr = &config->serv_addr;
	int fd = socket(PF_INET, SOCK_STREAM, 0);
	int reuse = 1;
	if (fd < 0)
		ERR("socket");
	/* http://stackoverflow.com/questions/14388706/socket-options-so-reuseaddr-and-so-reuseport-how-do-they-differ-do-they-mean-t */
	/* \todo Check if other setsockopt options would be helpful. See: man 7 ip */
	if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)))
		ERR("setsockopt");
	/** \note Use `SUN_LEN` macro in case of UNIX socket domain! */
	if (connect(fd, (struct sockaddr*)addr, sizeof(struct sockaddr_in)) < 0) {
		if (errno == EINTR) {
			return poll_for_asynchronous_connection(fd);
		} else if (errno == ECONNREFUSED) {
			syslog(LOG_WARNING, "Server is not running on specified "
			       "port or connection was refused by server");
			return -1;
		} else {
			ERR("connect");
		}
	}
	return fd;
}

int send_hello_to_server(int fd) {
	const char *msg = "Ala ma kota, a kot ma ale"; /* \todo */
	sleep(10); /* \todo temporary */
	if (bulk_send(fd, msg, strlen(msg), 0) < 0)
		ERR("bulk_send failed - can't send data to server");
	return 0;
}
