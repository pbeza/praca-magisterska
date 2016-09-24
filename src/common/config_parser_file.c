/** \file
 * Implementation of common functions accessing configuration file of the client
 * or server. Configuration read from configuration file will overwrite static
 * `INIT_CONFIG` but can be overwritten by parameters passed via `argv[]`.
 */
#include <libconfig.h>
#include <syslog.h>

#include "config_parser_file.h"

#define CONFIG_FILE_PORT		"PORT"

static void read_port(const config_t *config, base_config_t *base_config) {
	int port;

	if (is_option_set(base_config, PORT_OPTION_ID))
		return;

	if (config_lookup_int(config, CONFIG_FILE_PORT, &port) == CONFIG_FALSE)
		syslog(LOG_WARNING, "Failed to read port from config file");
	else
		syslog(LOG_DEBUG, "Port %d read from config file", port);

	base_config->port = port;
}

int common_read_config_from_file(const config_t *config, base_config_t *base_config) {
	read_port(config, base_config);
	return 0;
}

void print_no_file_msg_conf(const char *file) {
	printf("Error parsing configuration file. "
	       "File '%s' doesn't exist or has insufficient read rights.\n",
	       file);
}
