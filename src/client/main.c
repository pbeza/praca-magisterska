/** \file
 * Client's main file.
 */
#include <stdlib.h>
#include <unistd.h>

#include "common/daemonize.h"
#include "common/security.h"
#include "config_parser.h"
#include "connection.h"
#include "security.h"

static int run_protocol(SSL *ssl, int socket) {
	if (send_hello_to_server(ssl, socket) < 0) {
		syslog(LOG_ERR, "Can't send data to server");
		return -1;
	}
	return 0;
}

static int daemon_work(const base_config_t *base_config) {
	client_config_t *config = (client_config_t*)base_config;
	security_config_t *security_config = SECURITY_CONFIG(config);
	int fd, ret = 0;

	if (set_sigint_handler() < 0) {
		syslog_errno("Setting SIGINT handler has failed");
		return -1;
	}

	if ((fd = connect_server(config)) < 0) {
		syslog(LOG_ERR, "Can't connect to server");
		return -1;
	}

	if (init_ssl_conn(security_config->ssl_ctx, &security_config->ssl, fd) < 0) {
		syslog(LOG_ERR, "Initializing SSL structure has failed");
		ret = -1;
		goto disconnect;
	}

	if (start_ssl_handshake(fd, security_config->ssl) < 0) {
		syslog(LOG_ERR, "SSL handshake with server has failed");
		ret = -1;
		goto cleanup_ssl;
	}

	syslog_ssl_summary(security_config->ssl);

	if (run_protocol(security_config->ssl, fd) < 0) {
		syslog(LOG_ERR, "Running protocol has failed");
		ret = -1;
	}

	if (bidirectional_shutdown_handshake(security_config->ssl) < 0) {
		syslog(LOG_ERR, "Shutdown handshake has failed");
		ret = -1;
	}

cleanup_ssl:
	SSL_free(security_config->ssl);

disconnect:
	if (disconnect_server(fd) < 0) {
		syslog(LOG_ERR, "Can't gracefully disconnect from server");
		ret = -1;
	}

	return ret;
}

/**
 * Wrapper for client's 3 main stages:
 * 1. SSL context initialization,
 * 2. work,
 * 3. SSL context cleanup.
 */
static int run(client_config_t *config) {
	int ret = 0;
	security_config_t *security_config = SECURITY_CONFIG(config);

	if (init_ssl_ctx(security_config) < 0) {
		fprintf(stderr, "Can't initialize OpenSSL.\n");
		return -1;
	}

	if (daemonize((const base_config_t*)config, daemon_work) < 0) {
		syslog(LOG_ERR, "Client work has failed");
		ret = -1;
	}

	if (cleanup_ssl_ctx(security_config->ssl_ctx) < 0) {
		syslog_ssl_err("Cleaning up SSL context has failed");
		return -1;
	}

	return ret;
}

/**
 * Main client's function.
 *
 * \note Note that all messages, both warnings, errors, debug and others, are
 * logged via `syslog` after successful daemonization. Before daemonization
 * mainly `stdout` and `stderr` are used.
 */
int main(int argc, char** argv) {
	client_config_t config = INIT_CONFIG;

	openlog(PROJECT_NAME, LOG_PID | LOG_CONS | LOG_ODELAY, LOG_USER);
	syslog(LOG_INFO, "Starting client. Hello!");

	if (load_config(argc, argv, &config) < 0) {
		syslog(LOG_INFO, "Loading configuration has failed");
	} else if (run(&config) < 0)
		syslog(LOG_ERR, "Running client has failed");

	syslog(LOG_INFO, "Exiting client. Bye!");
	closelog();

	return EXIT_SUCCESS;
}
