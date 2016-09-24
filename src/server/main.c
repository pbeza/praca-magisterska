/** \file
 * Server's main file.
 */
#include <stdio.h>
#include <stdlib.h>
#include <syslog.h>

#include "common/daemonize.h"
#include "config_parser.h"
#include "main_loop.h"
#include "security.h"

/**
 * Daemon's work. This function is being ran even if daemonization was turned
 * off. From now on, logging is done via `syslog` _only_.
 *
 * \note \p base_config parameter must be casted to \a server_config since
 * this function is used as a callback in common for both client and server
 * daemonization library.
 */
static int daemon_work(const base_config_t *base_config) {
	const server_config_t *config = (const server_config_t*)base_config;

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
 * Wrapper for server's 3 main stages:
 * 1. SSL context initialization,
 * 2. work,
 * 3. SSL context cleanup.
 */
static int run(server_config_t *config) {
	int ret = 0;
	security_config_t *security_config = SECURITY_CONFIG(config);

	if (init_ssl_ctx(security_config) < 0) {
		fprintf(stderr, "Can't initialize OpenSSL.\n");
		return -1;
	}

	if (daemonize((const base_config_t*)config, daemon_work) < 0) {
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

	if (load_config(argc, argv, &config) < 0)
		syslog(LOG_INFO, "Loading config has failed");
	else if (run(&config) < 0)
		syslog(LOG_ERR, "Running server has failed");

	syslog(LOG_INFO, "Exiting server. Bye!");
	closelog();

	return EXIT_SUCCESS;
}
