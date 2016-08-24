/** \file
 * Client's `argv` parser.
 */
#ifndef _CLIENT_ARGV_PARSER_H
#define _CLIENT_ARGV_PARSER_H

#include <netinet/in.h>

#include "common/argv_parser.h"
#include "config.h"

#define HELP_PREFIX			"Usage: " PROJECT_NAME " [ options ] server_ipv4\n\n"\
					"Starts client which connects to specified server to synchronize"\
					"installed applications and their configuration.\n\n"\
					"Options:\n\n"

/**
 * Client configuration - both precompiled and parsed from `argv`.
 */
typedef struct client_config_t {
	common_config_t base_config;
	struct sockaddr_in serv_addr;
	char *serv_ip_str;
} client_config_t;

/**
 * Precompiled application configuration ie. configuration before parsing `argv`.
 */
static const client_config_t INIT_CONFIG = {
	.base_config = INIT_BASE_CONFIG,
	.serv_addr = { 0 },
	.serv_ip_str = NULL
};

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse(int argc, char **argv, client_config_t *config);

#endif
