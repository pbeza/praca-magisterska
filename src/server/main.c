/** \file
 * Server's main file.
 */
#include <stdlib.h>
#include <unistd.h>

#include "argv_parser.h"
#include "common/daemonize.h"
#include "main_loop.h"
#include "security.h"

/**
 * Path to file with daemon's PID to disallow multiple instances of the daemon.
 * See: http://www.pathname.com/fhs/2.2/fhs-5.13.html
 *
 * \todo Need root to access `/var/run` directory.
 */
#define UNIQ_DAEMON_INSTANCE_PID_PATH	"/tmp/" PROJECT_NAME ".pid"
/*#define UNIQ_DAEMON_INSTANCE_PID_PATH	"/var/run/" PROJECT_NAME ".pid"*/

/**
 * Daemon's work. Unless daemonization was switched off, this function is being
 * ran in daemon's process. From now on, logging is done via `syslog` _only_.
 */
static int daemon_work(const server_config_t *config) {
	if (set_sigint_handler() < 0) {
		syslog_errno("Setting SIGINT handler has failed");
		return -1;
	}

	if (accept_clients(config) < 0) {
		syslog(LOG_ERR, "Critical fail in function accepting clients");
		return -1;
	}

	return 0;
}

/**
 * Start daemon if daemonization is not switched off. Ensure that only one
 * daemon can run and run daemon's work.
 * \todo Not daemonized application probably should use file with PID.
 */
static int server_work(const server_config_t *config) {
	const common_config_t *base_config = &config->base_config;
	int start_daemon = !is_dont_daemonize_set(base_config),
	    pid_fd, /* file with PID to allow one instance of daemon */
	    ret = 0;

	if (start_daemon && sysv_daemonize(UNIQ_DAEMON_INSTANCE_PID_PATH, &pid_fd) < 0) {
		fprintf(stderr, "Cannot create SysV daemon. Refer syslog for details.\n");
		return -1;
	}

	if (daemon_work(config) < 0) {
		syslog(LOG_ERR, "Daemon work has failed");
		ret = -1; /* need to close pid_fd if daemonized */
	}

	if (start_daemon && TEMP_FAILURE_RETRY(close(pid_fd)) < 0) {
		syslog_errno("Closing one instance PID-file has failed");
		return -1;
	}

	return ret;
}

/**
 * Wrapper for server's 3 main stages:
 * 1. SSL context initialization,
 * 2. work,
 * 3. cleanup.
 */
static int run(server_config_t *config) {
	int ret = 0;
	security_config_t *security_config = &config->security_config;

	if (init_ssl_ctx(security_config) < 0) {
		fprintf(stderr, "Can't initialize OpenSSL.\n");
		return -1;
	}

	if (server_work(config) < 0) {
		syslog(LOG_ERR, "Server work has failed");
		ret = -1;
	}

	if (cleanup_ssl_ctx(security_config->ssl_ctx) < 0) {
		syslog_ssl_err("Cleaning up SSL context has failed");
		return -1;
	}

	return ret;
}

/**
 * Main server's function.
 *
 * \note Note that all messages, both warnings, errors, debug and others, are
 * logged via `syslog` after successful daemonization. Before daemonization
 * mainly `stdout` and `stderr` are used.
 */
int main(int argc, char **argv) {
	server_config_t config = INIT_CONFIG;

	openlog(PROJECT_NAME, LOG_PID | LOG_CONS | LOG_ODELAY, LOG_USER);
	syslog(LOG_INFO, "Starting server. Hello!");

	if (parse(argc, argv, &config) < 0) {
		syslog(LOG_INFO, "Parser decided to exit - "
		       "refer stdout/stderr for more details");
	} else {
		if (run(&config) < 0)
			syslog(LOG_ERR, "Running server has failed");
	}

	syslog(LOG_INFO, "Exiting server. Bye!");
	closelog();

	return EXIT_SUCCESS;
}
