/** \file
 * Server's main file.
 */
#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <stdlib.h>
#include <unistd.h>

#include "argv_parser.h"
#include "common/daemonize.h"
#include "main_loop.h"

/**
 * Path to file with daemon's PID to disallow multiple instances of daemon.
 * See: http://www.pathname.com/fhs/2.2/fhs-5.13.html
 *
 * \todo Need root to access /var/run directory.
 */
#define UNIQ_DAEMON_PID_PATH		"/tmp/" PROJECT_NAME ".pid"
/* #define UNIQ_DAEMON_PID_PATH		"/var/run/" PROJECT_NAME ".pid" */

static void daemon_work(const server_config_t *config) {
	listen_clients(config);
}

static void server_work(const server_config_t *config) {
	const common_config_t *base_config = &(config->base_config);
	int pid_file_fd = 0; /* file with PID to allow one instance of daemon */
	if (!is_option_set(base_config->selected_options, DONT_DAEMONIZE_OPTION) &&
	    sysv_daemonize(UNIQ_DAEMON_PID_PATH, &pid_file_fd) < 0) {
		printf("Cannot create SysV daemon - check syslog for details\n");
	} else {
		daemon_work(config);
		if (TEMP_FAILURE_RETRY(close(pid_file_fd)) < 0)
			ERR("closing PID file");
	}
}

int main(int argc, char** argv) {
	server_config_t config = INIT_CONFIG;
	int exit = parse(argc, argv, &config);
	if (!exit) {
		openlog(PROJECT_NAME, LOG_PID | LOG_CONS | LOG_ODELAY, LOG_USER);
		server_work(&config);
		closelog();
	}
	return EXIT_SUCCESS;
}
