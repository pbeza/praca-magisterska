/** \file
 * Server's main file.
 */

#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <arpa/inet.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <syslog.h>
#include <unistd.h>

#include "common/daemonize.h"
#include "common/utils/common.h"
#include "common/utils/network.h"
#include "server_parser.h"

#define BACKLOG		MIN(32, SOMAXCONN)
#define MSGCOUNT	8

/*
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
	/ TODO Check if other setsockopt options would be helpful.
	   See: man 7 ip /
	if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)))
		ERR("setsockopt");
	if (bind(fd, (struct sockaddr*) &addr, sizeof(addr)) < 0)
		ERR("bind");
	if (listen(fd, BACKLOG) < 0)
		ERR("listen");
	return fd;
}

static int wait_for_client_msg(int csocket_fd){
	int is_set;
	fd_set rfds;
	FD_ZERO(&rfds);
	FD_SET(csocket_fd, &rfds);
	/ TODO poll is better for waiting for a single file descriptor /
	if (TEMP_FAILURE_RETRY(select(csocket_fd + 1, &rfds, NULL, NULL, NULL)) < 0)
		ERR("select");
	is_set = FD_ISSET(csocket_fd, &rfds);
	if(is_set < 0)
		ERR("FD_ISSET");
	return is_set;
}

static void listen_clients(const config_t *config) {
	ssize_t len;
	int port = config->port, ssocket_fd = listen_on_port(port);
	int csocket_fd, is_set;
	char buf[MSGCOUNT + 1], *ip;
	struct sockaddr caddr;
	struct sockaddr_in *caddr_in;
	socklen_t caddr_len;
	memset(buf, 0, sizeof(buf));

	syslog(LOG_INFO, "accepting connection...");

	csocket_fd = TEMP_FAILURE_RETRY(accept(ssocket_fd, &caddr, &caddr_len));
	if (csocket_fd < 0)
		ERR("accept");

	caddr_in = (struct sockaddr_in*)&caddr;
	ip = inet_ntoa(caddr_in->sin_addr);
	syslog(LOG_INFO, "connection accepted from client %s", ip);
	syslog(LOG_INFO, "waiting for client message");

	is_set = wait_for_client_msg(csocket_fd);
	errno = 0;
	if (is_set == 0 || (len = bulk_read(csocket_fd, buf, MSGCOUNT)) <= 0) {
		if (len < 0)
			ERR("read");
		if (TEMP_FAILURE_RETRY(close(csocket_fd)) < 0)
			ERR("close");
		syslog(LOG_NOTICE, "connection probably lost");
	}
	printf("incoming msg:\n%s", buf);

	if (TEMP_FAILURE_RETRY(close(csocket_fd)) < 0 && errno != EBADF)
		ERR("close");
	if (TEMP_FAILURE_RETRY(close(ssocket_fd)) < 0)
		ERR("close");
}*/

static void server_work(const config_t *config) {
	UNUSED(config);
	if (sysv_daemonize() < 0)
		printf("Cannot create SysV daemon - check syslog for details\n");
	/*else*/
	/* listen_clients(config); */
}

int main(int argc, char** argv) {
	config_t config = INIT_CONFIG;
	int exit = parse_argv(argc, argv, &config);
	if (!exit)
		server_work(&config);
	return EXIT_SUCCESS;
}
