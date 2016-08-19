#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <arpa/inet.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>

#include "argv_parser.h"
#include "common/common.h"
#include "common/network.h"

#define BACKLOG				MIN(32, SOMAXCONN)
#define MSGCOUNT			8
#define POLL_TIMEOUT_MILLISECONDS	30 * 1000 /* \todo increase timeout */

static void init_sockaddr(struct sockaddr_in* addr, uint16_t port) {
	memset(addr, 0, sizeof(struct sockaddr_in));
	addr->sin_family = AF_INET;
	addr->sin_port = htons(port);
	addr->sin_addr.s_addr = htonl(INADDR_ANY);
}

static int listen_on_port(uint16_t port) {
	struct sockaddr_in addr;
	const int reuse = 1;
	int fd = socket(PF_INET, SOCK_STREAM, 0);
	if (fd < 0)
		ERR("socket");
	init_sockaddr(&addr, port);
	/* http://stackoverflow.com/questions/14388706/socket-options-so-reuseaddr-and-so-reuseport-how-do-they-differ-do-they-mean-t */
	/* \todo Check if other setsockopt options would be helpful. See: man 7 ip */
	if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)))
		ERR("setsockopt");
	if (bind(fd, (struct sockaddr*) &addr, sizeof(addr)) < 0)
		ERR("bind - check whether other daemon instance is running");
	if (listen(fd, BACKLOG) < 0)
		ERR("listen");
	return fd;
}

static int wait_for_client_msg(int csocket_fd) {
	int is_set;
	struct pollfd fds[1] = { 0 };
	fds[0].fd = csocket_fd;
	fds[0].events = POLLIN;
	is_set = TEMP_FAILURE_RETRY(poll(fds, ARRAY_LENGTH(fds),
					 POLL_TIMEOUT_MILLISECONDS));
	if (is_set < 0)
		ERR("poll");
	else if (!is_set)
		syslog(LOG_WARNING,
		       "Waiting for client's message has timed out after %dms",
		       POLL_TIMEOUT_MILLISECONDS);
	return is_set;
}

void listen_clients(const server_config_t *config) {
	ssize_t len;
	int port = config->base_config.port, ssocket_fd = listen_on_port(port);
	int csocket_fd, is_set;
	char buf[MSGCOUNT + 1] = { 0 }, *ip;
	struct sockaddr caddr = { 0 };
	struct sockaddr_in *caddr_in;
	socklen_t caddr_len = 0;
	syslog(LOG_INFO, "Accepting connection...");
	csocket_fd = TEMP_FAILURE_RETRY(accept(ssocket_fd, &caddr, &caddr_len));
	if (csocket_fd < 0)
		ERR("accept");
	caddr_in = (struct sockaddr_in*)&caddr;
	ip = inet_ntoa(caddr_in->sin_addr);
	syslog(LOG_INFO, "Connection accepted from client %s,"
	       "waiting for client message for %dms", ip,
	       POLL_TIMEOUT_MILLISECONDS);
	is_set = wait_for_client_msg(csocket_fd);
	if (is_set == 0 || (len = bulk_recv(csocket_fd, buf, MSGCOUNT, 0)) <= 0) {
		if (len < 0)
			ERR("read");
		syslog(LOG_NOTICE, "Connection probably lost");
	} else {
		syslog(LOG_DEBUG, "Incoming msg:%s", buf);
	}
	if (TEMP_FAILURE_RETRY(close(csocket_fd)) < 0)
		ERR("close");
	if (TEMP_FAILURE_RETRY(close(ssocket_fd)) < 0)
		ERR("close");
}
