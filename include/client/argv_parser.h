/** \file
 * Client's `argv` parser.
 */
#ifndef _CLIENT_ARGV_PARSER_H
#define _CLIENT_ARGV_PARSER_H

#include "common/argv_parser.h"
#include "config.h"

/**
 * Beginning of the help section.
 */
#define HELP_PREFIX			"Usage: " PROJECT_NAME " [ options ]\n\n"\
					"Starts client which connects to specified server to synchronize installed applications and their configuration.\n\n"\
					"Options:\n\n"

/**
 * @{ Options' description.
 */
#define DESC_OPTION_VERSION		"Print client's version number."
#define DESC_OPTION_PORT		"Server's listening port number."

/** @}
 * Options string for `getopt`.
 */
#define GETOPT_STRING			":hvp:d"

/**
 * Client configuration - both precompiled and parsed from `argv`.
 */
typedef struct client_config_t {
	common_config_t base_config;
} client_config_t;

/**
 * Precompiled application configuration ie. configuration before parsing `argv`.
 */
static const client_config_t INIT_CONFIG = {
	.base_config = {
		.selected_options = 0,
		.port = DEFAULT_SERVER_LISTENING_PORT
	}
};

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse_argv(int argc, char **argv, client_config_t *config);

#endif
