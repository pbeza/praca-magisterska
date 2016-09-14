/** \file
 * Client's `argv` parser.
 */
#ifndef _CLIENT_ARGV_PARSER_H
#define _CLIENT_ARGV_PARSER_H

#include <netinet/in.h>

#include "common/argv_parser.h"
#include "config.h"
#include "security.h"

#define HELP_PREFIX			"Usage: " PROJECT_NAME " [ options ] server_ipv4\n\n"\
					"Starts client which connects to specified server to synchronize installed\n"\
					"applications and their configuration.\n\n"\
					"Options:\n\n"

/**
 * Client configuration - both precompiled and parsed from `argv`.
 */
typedef struct client_config_t {
	/**
	 * Basic application configuration. `common_config_t` structure is used
	 * by both server and client.
	 *
	 * \warning This MUST be first member of the struct because we take
	 * advantage of C primitive inheritance. C says that no padding appears
	 * before the first member of a struct. For more details refer:
	 * http://stackoverflow.com/questions/1114349/struct-inheritance-in-c
	 */
	const common_config_t base_config;
	/**
	 * Client's OpenSSL configuration.
	 */
	security_config_t security_config;
	/**
	 * Server address, eg. IP number and port.
	 */
	struct sockaddr_in serv_addr;
	/**
	 * Pointer to `argv[]` parameter with server's IP.
	 */
	char *serv_ip_str;
} client_config_t;

/**
 * Precompiled application configuration ie. configuration before parsing `argv`.
 */
static const client_config_t INIT_CONFIG = {
	.base_config = INIT_BASE_CONFIG,
	.security_config = INIT_SECURITY_CONFIG,
	.serv_addr = { 0 },
	.serv_ip_str = NULL
};

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse(int argc, char **argv, client_config_t *config);

#endif
