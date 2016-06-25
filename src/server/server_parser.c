#include <getopt.h>
#include <stdio.h>

#include "common/utils/options.h"
#include "server_parser.h"

static void test_save_fun(const struct option_t* option, const char* value, void* config) {
	UNUSED(option);
	config_t* c = (config_t*) config;
	c->test_val = atoi(value);
}

static void print_version() {
	printf(PROJECT_NAME " " PROJECT_VERSION " built for " HOST_SYSTEM_PROCESSOR ".\n\n");
	printf(COPYRIGHT);
	printf("Written by " AUTHOR ".\n");
}

void parse_argv(int argc, char** argv, config_t* config) {
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
		OPTION(TEST_OPTION,
		       SHORT_OPTION_TEST,
		       LONG_OPTION_TEST,
		       DESC_OPTION_TEST,
		       OPTION_VALUE_NAME,
		       test_save_fun)
	};
	const int n = ARRAY_LENGTH(options);
	parse(argc, argv, GETOPT_STRING, options, &(config->selected_options), (void*)config, n);
	if (IS_SETBIT(config->selected_options, HELP_OPTION))
		print_help(options, n, HELP_PREFIX, HELP_POSTFIX);
	else if (IS_SETBIT(config->selected_options, VERSION_OPTION))
		print_version();
}