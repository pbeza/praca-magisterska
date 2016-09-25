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

int read_path_from_conf(const config_t *config, base_config_t *base_config,
			int option_id, const char *config_var_path,
			char *config_save_path, int is_required);

#endif
