#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <poll.h>
#include <stdlib.h>
#include <syslog.h>
#include <unistd.h>

#include "client_thread.h"
#include "common/common.h"
#include "common/network.h"

#define POLL_TIMEOUT_MILLISECONDS	30 * 1000 /* \todo increase timeout */
#define MSGCOUNT			8

static int wait_for_client_msg(int csocket) {
	int is_set;
	struct pollfd fds[1] = { 0 };
	fds[0].fd = csocket;
	fds[0].events = POLLIN;
	is_set = TEMP_FAILURE_RETRY(poll(fds, ARRAY_LENGTH(fds), POLL_TIMEOUT_MILLISECONDS));
	if (is_set < 0) {
		ERR("poll");
	} else if (!is_set) {
		syslog(LOG_WARNING,
		       "Waiting for client's message has timed out after %dms",
		       POLL_TIMEOUT_MILLISECONDS);
		return -1;
	}
	return 0;
}

void* thread_work(thread_arg_t *thread_arg) {
	ssize_t len;
	char buf[MSGCOUNT + 1] = { 0 };
	int csocket = thread_arg->csocket;
	int ret = wait_for_client_msg(csocket);

	if (ret || (len = bulk_recv(csocket, buf, MSGCOUNT, 0)) <= 0) {
		if (len < 0)
			syslog(LOG_CRIT, "Error during reading client's socket "
			       "which returned -1; details: %m");
		else
			syslog(LOG_NOTICE, "Connection probably lost");
	} else {
		syslog(LOG_DEBUG, "Incoming msg:%s", buf);
	}

	return NULL;
}

