#include <stdio.h>
#include <syslog.h>

#include "config_parser.h"

#include "config.h"
#include "config_parser_argv.h"
#include "config_parser_file.h"

int load_config(int argc, char **argv, server_config_t *server_config) {
	/* Need to parse argv[] first to obtain config file path if provided */
	if (read_config_from_argv(argc, argv, server_config) < 0) {
		syslog(LOG_INFO, "Reading config from argv[] has failed");
		return -1;
	}

	if (read_config_from_file(server_config) < 0) {
		fprintf(stderr, "Reading configuration from file has failed. "
			"Check if file exists. Refer syslog for more details.\n");
		return -1;
	}

	return 0;
}
