/** \file
 * Client's main file.
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

static void daemon_work(const client_config_t *config) {
	int fd = connect_server(config);
	if (fd < 0) {
		syslog(LOG_WARNING, "Can't connect to server - aborting");
		return;
	}
	if (send_hello_to_server(fd) < 0) {
		syslog(LOG_ERR, "Can't send data to server");
		return;
	}
}

static void client_work(const client_config_t *config) {
	const common_config_t *base_config = &config->base_config;
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
	client_config_t config = INIT_CONFIG;
	int exit = parse(argc, argv, &config);
	if (!exit) {
		openlog(PROJECT_NAME, LOG_PID | LOG_CONS | LOG_ODELAY, LOG_USER);
		syslog(LOG_INFO, "Starting client");
		client_work(&config);
		syslog(LOG_INFO, "Exiting client - bye!");
		closelog();
	}
	return EXIT_SUCCESS;
}
