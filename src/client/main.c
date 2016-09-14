/** \file
 * Client's main file.
 */
#include <stdlib.h>
#include <unistd.h>

#include "argv_parser.h"
#include "common/daemonize.h"
#include "common/security.h"
#include "connection.h"
#include "security.h"

/**
 * Path to file with daemon's PID to disallow multiple instances of the daemon.
 * See: http://www.pathname.com/fhs/2.2/fhs-5.13.html
 *
 * \todo Need root to access `/var/run` directory.
 */
#define UNIQ_DAEMON_INSTANCE_PID_PATH	"/tmp/" PROJECT_NAME ".pid"
/*#define UNIQ_DAEMON_INSTANCE_PID_PATH	"/var/run/" PROJECT_NAME ".pid"*/

static int run_protocol(SSL *ssl, int socket) {
	if (send_hello_to_server(ssl, socket) < 0) {
		syslog(LOG_ERR, "Can't send data to server");
		return -1;
	}
	return 0;
}

static int daemon_work(client_config_t *client_config) {
	const struct sockaddr_in *addr = &client_config->serv_addr;
	security_config_t *security_config = &client_config->security_config;
	int fd, ret = 0;

	if ((fd = connect_server(addr)) < 0) {
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

static int client_work(client_config_t *config) {
	const common_config_t *base_config = &config->base_config;
	int start_daemon = !is_dont_daemonize_set(base_config),
	    pid_fd,
	    ret = 0;

	if (start_daemon && sysv_daemonize(UNIQ_DAEMON_INSTANCE_PID_PATH, &pid_fd) < 0) {
		fprintf(stderr, "Cannot create SysV daemon. Check syslog for details.\n");
		return -1;
	}

	if (daemon_work(config) < 0) {
		syslog(LOG_ERR, "Daemon work has failed");
		ret = -1;
	}

	if (start_daemon && TEMP_FAILURE_RETRY(close(pid_fd)) < 0) {
		syslog_errno("Closing one instance PID-file has failed");
		return -1;
	}

	return ret;
}

/**
 * Wrapper for client's 3 main stages:
 * 1. SSL context initialization,
 * 2. work,
 * 3. cleanup.
 */
static int run(client_config_t *config) {
	int ret = 0;

	if (init_ssl_ctx(&config->security_config) < 0) {
		fprintf(stderr, "Can't initialize OpenSSL.\n");
		return -1;
	}

	if (client_work(config) < 0) {
		syslog(LOG_ERR, "Client work has failed");
		ret = -1;
	}

	if (cleanup_ssl_ctx(&config->security_config) < 0) {
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

	if (parse(argc, argv, &config) < 0) {
		syslog(LOG_INFO, "Parser decided to exit - "
		       "refer stdout/stderr for more details");
	} else {
		if (run(&config) < 0)
			syslog(LOG_ERR, "Running client has failed");
	}

	syslog(LOG_INFO, "Exiting client. Bye!");
	closelog();

	return EXIT_SUCCESS;
}
