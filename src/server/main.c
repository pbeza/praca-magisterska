/** \file
 * Server's main file.
 */

#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <errno.h>
#include <unistd.h>

#include "common/daemonize.h"
#include "main_loop.h"
#include "parser.h"

/**
 * Path to file with daemon's PID to disallow multiple instances of daemon.
 * See: http://www.pathname.com/fhs/2.2/fhs-5.13.html
 * TODO Need root to access /var/run directory.
 */
/* #define UNIQ_DAEMON_PID_PATH		"/var/run/" PROJECT_NAME ".pid" */
#define UNIQ_DAEMON_PID_PATH		"/tmp/" PROJECT_NAME ".pid"

static void server_work(const config_t *config) {
	int pid_fd = 0;
	UNUSED(config);
	if (sysv_daemonize(UNIQ_DAEMON_PID_PATH, &pid_fd) < 0) {
		printf("Cannot create SysV daemon - check syslog for details\n");
	} else {
		listen_clients(config);
		if (TEMP_FAILURE_RETRY(close(pid_fd)) < 0)
			ERR("closing PID file");
	}
}

int main(int argc, char** argv) {
	config_t config = INIT_CONFIG;
	int exit = parse_argv(argc, argv, &config);
	if (!exit)
		server_work(&config);
	return EXIT_SUCCESS;
}
