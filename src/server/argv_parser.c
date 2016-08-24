#include <getopt.h>
#include <stdio.h>

#include "argv_parser.h"

#define DESC_OPTION_VERSION		"Print server's version number."

int parse(int argc, char **argv, server_config_t *config) {
	const option_t allowed_options[] = {
		OPTION(HELP_OPTION, SHORT_OPTION_HELP, LONG_OPTION_HELP,
		       DESC_OPTION_HELP, NULL, NULL),
		OPTION(VERSION_OPTION, SHORT_OPTION_VERSION,
		       LONG_OPTION_VERSION, DESC_OPTION_VERSION, NULL, NULL),
		OPTION(PORT_OPTION, SHORT_OPTION_PORT, LONG_OPTION_PORT,
		       DESC_OPTION_PORT, OPTION_VALUE_NAME, port_save_fun),
		OPTION(DONT_DAEMONIZE_OPTION, SHORT_OPTION_DONT_DAEMONIZE,
		       LONG_OPTION_DONT_DAEMONIZE, DESC_OPTION_DONT_DAEMONIZE,
		       NULL, NULL)
	};
	const int n = ARRAY_LENGTH(allowed_options);
	return common_parse(argc, argv, allowed_options, (void*)config, n);
}
