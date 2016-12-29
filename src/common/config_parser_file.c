/** \file
 * Implementation of common functions accessing configuration file of the client
 * or server. Configuration read from configuration file will overwrite static
 * `INIT_CONFIG` but can be overwritten by parameters passed via `argv[]`.
 */
#include <libconfig.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>

#include "config_parser_file.h"

static int read_port(const config_t *config, base_config_t *base_config) {
	int port;

	if (is_option_set(base_config, PORT_OPTION_ID))
		return 0;

	if (config_lookup_int(config, CONFIG_FILE_PORT, &port) == CONFIG_FALSE) {
		syslog(LOG_WARNING, "Server's port number is probably not "
		       "provided in configuration file. Default port %d will "
		       "be used.", base_config->port);
		return 0;
	}

	if (port < MIN_PORT_NUMBER || port > MAX_PORT_NUMBER) {
		fprintf(stderr, "Server's port number %d loaded from "
		       "configuration file is out of accepted range [%d, %d].\n",
		       port, MIN_PORT_NUMBER, MAX_PORT_NUMBER);
		return -1;
	}

	syslog(LOG_INFO, "Server's port %s = %d successfully loaded from "
	       "configuration file", CONFIG_FILE_PORT, port);

	base_config->port = port;

	return 0;
}

int common_read_config_from_file(const config_t *config, base_config_t *base_config) {
	const char *config_path = base_config->config_file_path;

	syslog(LOG_DEBUG, "Reading '%s' configuration file", config_path);

	if (read_port(config, base_config) < 0) {
		syslog(LOG_ERR, "Reading server's port from configuration file has failed");
		return -1;
	}

	return 0;
}

static int read_str_from_conf(const config_t *config,
			      const char *config_var_path,
			      char *config_save_path,
			      int is_required,
			      const char **str) {

	if (config_lookup_string(config, config_var_path, str) == CONFIG_FALSE) {
		if (is_required) {
			fprintf(stderr, "Required option '%s' is not set in "
			       "configuration file.\n", config_var_path);
			return -1;
		}

		syslog(LOG_INFO, "Option '%s' not provided in configuration "
		       "file. Default value '%s' will be used.\n",
		       config_var_path, config_save_path);
	} else {
		strncpy(config_save_path, *str, PATH_MAX_LEN);
		syslog(LOG_INFO, "Setting %s = '%s' successfully loaded from "
		       "configuration file", config_var_path, config_save_path);
	}

	*str = config_save_path;

	return 0;
}

int read_file_path_from_conf(const config_t *config,
			     base_config_t *base_config,
			     int option_id,
			     const char *config_var_path,
			     char *config_save_path,
			     int is_required) {
	const char *path;

	/* Option already set via `argv[]`? `argv[]` takes precedence */
	if (option_id >= 0 && is_option_set(base_config, option_id))
		return 0;

	if (read_str_from_conf(config, config_var_path, config_save_path,
				is_required, &path) < 0)
		return -1;

	if (check_if_file_exists(path) < 0) {
		fprintf(stderr, "Error parsing configuration file. File '%s' "
			"read from '%s' variable doesn't exist or has "
			"insufficient read rights.\n",
			path, config_var_path);
		return -1;
	}

	return 0;
}

int read_dir_path_from_conf(const config_t *config,
			    base_config_t *base_config,
			    int option_id,
			    const char *config_var_path,
			    char *config_save_path,
			    int is_required) {
	const char *path;

	/* Option already set via `argv[]`? `argv[]` takes precedence */
	if (option_id >= 0 && is_option_set(base_config, option_id))
		return 0;

	if (read_str_from_conf(config, config_var_path, config_save_path,
				is_required, &path) < 0)
		return -1;

	if (check_if_dir_exists(path) < 0) {
		fprintf(stderr, "Error parsing configuration file. Directory "
			"'%s' read from '%s' variable doesn't exist or has "
			"insufficient read rights.\n",
			path, config_var_path);
		return -1;
	}

	return 0;
}
