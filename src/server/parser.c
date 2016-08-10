#include <getopt.h>
#include <stdio.h>

#include "common/utils/options.h"
#include "parser.h"

#define PORT_NUMBER_TOO_SMALL	-1
#define PORT_NUMBER_TOO_BIG	-2

static int port_save_fun(const struct option_t* option, const char* value, void* config) {
	int port = atoi(value), ret = 0;
	UNUSED(option);
	config_t* c = (config_t*) config;
	if (port < MIN_PORT_NUMBER)
		ret = PORT_NUMBER_TOO_SMALL;
	else if (port > MAX_PORT_NUMBER)
		ret = PORT_NUMBER_TOO_BIG;
	else
		c->port = port;
	return ret;
}

static void print_version() {
	printf(PROJECT_NAME " " PROJECT_VERSION
#ifdef DEBUG
	       " debug"
#endif
	       " built for " HOST_SYSTEM_PROCESSOR ".\n\n");
	printf(COPYRIGHT);
	printf("Written by " AUTHOR ".\n");
}

static int is_option_set(const config_t* config, option_code opt) {
	return IS_SETBIT(config->selected_options, opt);
}

int parse_argv(int argc, char** argv, config_t* config) {
	const option_t options[] = {
		OPTION(HELP_OPTION,
		       SHORT_OPTION_HELP,
		       LONG_OPTION_HELP,
		       DESC_OPTION_HELP,
		       NULL,
		       NULL),
		OPTION(VERSION_OPTION,
		       SHORT_OPTION_VERSION,
		       LONG_OPTION_VERSION,
		       DESC_OPTION_VERSION,
		       NULL,
		       NULL),
		OPTION(PORT_OPTION,
		       SHORT_OPTION_PORT,
		       LONG_OPTION_PORT,
		       DESC_OPTION_PORT,
		       OPTION_VALUE_NAME,
		       port_save_fun)
	};
	const int n = ARRAY_LENGTH(options);
	int ret = parse(argc, argv, GETOPT_STRING, options, &(config->selected_options), (void*)config, n);
	if (ret < 0)
		printf("Port number is too %s. "
		       "Port number must be integer from range [%d,%d].\n",
		       ret == PORT_NUMBER_TOO_SMALL ? "small" : "big",
		       MIN_PORT_NUMBER, MAX_PORT_NUMBER);
	else if (is_option_set(config, HELP_OPTION)) {
		print_help(options, n, HELP_PREFIX, HELP_POSTFIX);
		ret = -1;
	}
	else if (is_option_set(config, VERSION_OPTION)) {
		print_version();
		ret = -1;
	}
	return ret;
}
