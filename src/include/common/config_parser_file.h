/** \file
 * Common functions accessing configuration file of the client or server.
 * Configuration read from configuration file will overwrite static
 * `INIT_CONFIG` but can be overwritten by parameters passed via `argv[]`.
 */
#ifndef _COMMON_CONFIG_PARSER_FILE_H
#define _COMMON_CONFIG_PARSER_FILE_H

#include <libconfig.h>

#include "config.h"

/**
 * Macro reporting fatal (emergency) errors (via syslog) during reading
 * configuration file.
 */
#define syslog_config_file(config, err_msg)\
					(\
					syslog(LOG_ERR, "ERROR reading config file "\
					       "%s:%d - %s; details: %s\n",\
					       config_error_file(config),\
					       config_error_line(config),\
					       config_error_text(config),\
					       err_msg)\
					)

int common_read_config_from_file(const config_t *config, base_config_t *base_config);

void print_no_file_msg_conf(const char *file);

#endif
