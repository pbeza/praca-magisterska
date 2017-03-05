/** \file
 * Server's `argv[]` parser.
 */
#ifndef _SERVER_CONFIG_PARSER_ARGV_H
#define _SERVER_CONFIG_PARSER_ARGV_H

#include "common/config_parser_argv.h"

#include "config.h"

/**
 * Add application's allowed options, parse `argv[]` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int read_config_from_argv(int argc, char **argv, server_config_t *config);

#endif
