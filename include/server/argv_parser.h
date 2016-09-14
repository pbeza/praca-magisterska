/** \file
 * Server's `argv` parser.
 */
#ifndef _SERVER_ARGV_PARSER_H
#define _SERVER_ARGV_PARSER_H

#include "common/argv_parser.h"
#include "config.h"
#include "security.h"

/**
 * First part of the `--help` section.
 */
#define HELP_PREFIX			"Usage: " PROJECT_NAME " [ options ]\n\n"\
					"Starts server providing synchronization of applications' "\
					"packages and configuration for clients.\n\n"\
					"Options:\n\n"
/**
 * Options' IDs. Refer common \a option_code for more details.
 */
typedef enum {
	CERTIFICATE_PATH_OPTION_ID = __LAST_COMMON_OPTION_ID,
	PRIVATE_KEY_PATH_OPTION_ID,
	PRIVATE_KEY_PASS_OPTION_ID
} server_option_code;


/**
 * Server configuration - both precompiled and parsed from `argv`.
 * \warning This configuration is shared by threads talking with client.
 */
typedef struct server_config_t {
	const common_config_t base_config;
	security_config_t security_config;
} server_config_t;

/**
 * Precompiled application configuration ie. configuration before parsing `argv`.
 */
static const server_config_t INIT_CONFIG = {
	.base_config = INIT_BASE_CONFIG,
	.security_config = INIT_SECURITY_CONFIG
};

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse(int argc, char **argv, server_config_t *config);

#endif
