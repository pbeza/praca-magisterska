/** \file
 * Implementation of establishing connection with server within client's daemon.
 */
#include <netdb.h>
#include <poll.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "connection.h"

#include "common/misc.h"
#include "common/security.h"

#define POLL_TIMEOUT_MILLISECONDS	10 * 1000
#define MAX_SSL_WRITE_RETRIES		5

/**
 * If `connect()` was interrupted by `EINTR`, connection is established
 * asynchronously. This function handles this troublesome case.
 */
static int poll_for_asynchronous_connection(int fd) {
	int is_set, status, ret = -1;
	socklen_t size = sizeof(int);
	struct pollfd fds[] = {
		{ .fd = fd, .events = POLLIN }
	};

	is_set = TEMP_FAILURE_RETRY(poll(fds, ARRAY_LENGTH(fds), POLL_TIMEOUT_MILLISECONDS));

	if (is_set < 0) {
		syslog_errno("poll() returned negative number");
	} else if (is_set) {
		if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &status, &size) < 0)
			syslog_errno("getsockopt() has failed");
		else if (status)
			syslog(LOG_ERR, "getsockopt() reports failure");
		else
			ret = 0;
	} else {
		syslog(LOG_WARNING, "Polling for establishing connection has "
		       "timed out after %dms", POLL_TIMEOUT_MILLISECONDS);
	}

	return ret;
}

static int try_connect_server(int fd, struct sockaddr *addr, socklen_t addrlen) {
	if (connect(fd, addr, addrlen) < 0) {
		if (errno == EINTR) {
			syslog(LOG_DEBUG, "EINTR while connect(); polling...");
			return poll_for_asynchronous_connection(fd);
		} else if (errno == ECONNREFUSED) {
			syslog(LOG_WARNING, "ECONNREFUSED: probably server is "
			       "not running on specified port or connection "
			       "was refused by server");
			return -1;
		} else {
			syslog_errno("Connection with server has failed");
			return -1;
		}
	}

	return 0;
}

static int create_socket() {
	int reuse = 1, fd;

	if ((fd = socket(PF_INET, SOCK_STREAM, 0)) < 0) {
		syslog_errno("Failed to create client's socket");
		return -1;
	}

	if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse))) {
		syslog_errno("setsockopt() on server's socket has failed");
		if (TEMP_FAILURE_RETRY(close(fd)) < 0)
			syslog_errno("Can't close server's socket");
		return -1;
	}

	return fd;
}

/**
 * Converts server's address string representation to `sockaddr` structure,
 * tries to connect to server and saves server's address in \p config.
 * \note Learn more: http://long.ccaba.upc.es/long/045Guidelines/eva/ipv6.html
 */
int connect_server(client_config_t *config) {
	int fd, err;
	char port_str[8];
	struct addrinfo *srv_info, *iterator, hints;
	struct sockaddr *addr = &config->serv_addr;

	if ((fd = create_socket()) < 0) {
		syslog(LOG_ERR, "Failed to create client's socket");
		return -1;
	}

	memset(&hints, 0, sizeof(struct addrinfo));
	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = AI_CANONNAME | AI_NUMERICSERV | AI_ADDRCONFIG;

	/*memset(addr, 0, sizeof(struct sockaddr));
	addr->sin_family = AF_INET;
	addr->sin_port = htons(port);*/

	snprintf(port_str, ARRAY_LENGTH(port_str), "%d", (int)PORT(config));

	/* The getaddrinfo() and getnameinfo() functions are preferred over the
	 * gethostbyaddr() and gethostbyname() functions. */

	err = getaddrinfo(config->serv_addr_str, port_str, &hints, &srv_info);
	if (err) {
		fprintf(stderr, "Unable to resolve server address.\n");
		syslog(LOG_ERR, "Can't resolve server address read from argv "
		       "using getaddrinfo(). Details: %s.",
		       err == EAI_SOCKTYPE ? strerror(errno) : gai_strerror(err));
		goto cleanup_socket;
	}

	for (iterator = srv_info; iterator != NULL; iterator = iterator->ai_next) {
		if (try_connect_server(fd, iterator->ai_addr, iterator->ai_addrlen) < 0)
			syslog(LOG_WARNING, "Can't connect to server using address '%s'",
			       srv_info->ai_canonname);
		else
			break;
	}

	freeaddrinfo(srv_info);

	if (!iterator) {
		syslog(LOG_ERR, "Failed to connect to server");
		goto cleanup_socket;
	}

	*addr = *srv_info->ai_addr;

	return fd;

cleanup_socket:
	if (TEMP_FAILURE_RETRY(close(fd)) < 0)
		syslog_errno("Can't close server's socket");

	return -1;
}

int disconnect_server(int socket) {
	if (TEMP_FAILURE_RETRY(close(socket)) < 0) {
		syslog_errno("Can't close() client's socket");
		return -1;
	}
	return 0;
}

/**
 * \todo This is very simplified communication model for testing SSL connection.
 * TODO TODO TODO
 */
int send_hello_to_server(SSL *ssl, int socket) {
	int ret, retries;
	const char *msg = "Ala ma kota, a kot ma ale";

	for (retries = 0; retries < MAX_SSL_WRITE_RETRIES; retries++) {
		sleep(6); /* \todo Temporary to test server */

		if ((ret = SSL_write(ssl, msg, strlen(msg))) > 0) {
			syslog(LOG_DEBUG, "SSL_write() successful, %d bytes sent", ret);
			return 0;
		} else if (ret < 0) {
			syslog_ssl_err("SSL_write() = -1, error or action must be taken");
		} else {
			if (SSL_get_error(ssl, ret) == SSL_ERROR_ZERO_RETURN) {
				syslog(LOG_INFO, "Connection was closed "
				       "cleanly during SSL_write()");
				return -1;
			}
			syslog_ssl_err("SSL_write() error, probably connection was closed");
		}

		if ((ret = handle_ssl_error_want(ret, ssl, socket)) < 0) {
			syslog(LOG_ERR, "Trying to handle SSL_write() error has failed");
			return -1;
		}
	}

	if (retries >= MAX_SSL_WRITE_RETRIES)
		syslog(LOG_ERR, "Maximum number %d of SSL_write() retries "
		       "reached, giving up", MAX_SSL_WRITE_RETRIES);

	return -1;
}
