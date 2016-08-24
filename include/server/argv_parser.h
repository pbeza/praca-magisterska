/** \file
 * Server's `argv` parser.
 */
#ifndef _SERVER_ARGV_PARSER_H
#define _SERVER_ARGV_PARSER_H

#include "common/argv_parser.h"
#include "config.h"

#define HELP_PREFIX			"Usage: " PROJECT_NAME " [ options ]\n\n"\
					"Starts server providing synchronization of applications' "\
					"packages and configuration for clients.\n\n"\
					"Options:\n\n"

/**
 * Server configuration - both precompiled and parsed from `argv`.
 */
typedef struct server_config_t {
	common_config_t base_config;
} server_config_t;

/**
 * Precompiled application configuration ie. configuration before parsing `argv`.
 */
static const server_config_t INIT_CONFIG = {
	.base_config = INIT_BASE_CONFIG
};

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse(int argc, char **argv, server_config_t *config);

#endif
