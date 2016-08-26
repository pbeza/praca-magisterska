#include <assert.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "argv_parser.h"

/**
 * Minimum allowed port number accepted by both server's and client's parser.
 */
#define MIN_PORT_NUMBER			1025

/**
 * Maximum allowed port number accepted by both server's and client's parser.
 */
#define MAX_PORT_NUMBER			65535

/**
 * Parser `getopt` return code in case of missing option's value.
 */
#define PARSER_MISSING_VALUE		':'

/**
 * Parser `getopt` return code in case of unrecognized option.
 */
#define PARSER_UNRECOGNIZED_OPTION	'?'

/**
 * Common message for all parser's warning messages.
 */
#define CHECK_MANUAL_MSG		"Check manual for usage help."

/**
 * Message about lack of support for long options in `argv` when POSIX
 * compliance is required.
 */
#ifdef POSIXLY_CORRECT
#define POSIXLY_CORRECT_LONG_OPTIONS_MSG"Note: Long options are not supported in this build.\n"
#else
#define POSIXLY_CORRECT_LONG_OPTIONS_MSG
#endif

/**
 * Print missing value message when some option requires lacking argument and exit.
 */
static void print_missing_value() {
	/** \note `getopt_long` doesn't store error in `optopt` in opposite to `getopt` */
	fprintf(stderr,
#ifndef POSIXLY_CORRECT
	"Missing operand. " CHECK_MANUAL_MSG "\n"
#else
	"Option -%c requires an operand. " CHECK_MANUAL_MSG "\n", optopt
#endif
	);
	closelog();
	exit(EXIT_FAILURE);
}

/**
 * Print unrecognized option value when option is not allowed and exit.
 */
static void print_unrecognized_option() {
	fprintf(stderr,
#ifndef POSIXLY_CORRECT
	"Unrecognized option detected. " CHECK_MANUAL_MSG "\n"
#else
	"Unrecognized option -%c. " CHECK_MANUAL_MSG "\n", optopt
#endif
	);
	closelog();
	exit(EXIT_FAILURE);
}

static void print_version(const char *project_name, const char *project_version) {
	printf("%s %s"
#ifdef DEBUG
	       " debug"
#endif
	       " built for " HOST_SYSTEM_PROCESSOR ".\n\n",
	       project_name, project_version);
	printf(COPYRIGHT);
	printf("Written by " AUTHOR ".\n");
}

/**
 * For given short option \p opt, find \ref option_t.save action in \p options
 * array (of length \p n) and execute it. Set \ref option_t.id-th bit in
 * \p selected_options integer, to indicate that this option is active.
 */
static int save_option(const option_t *options, int opt,
		       uint32_t *selected_options, void *config, const int n) {
	int i, ret = 0;
	const option_t *c;
	for (i = 0; i < n; i++) {
		c = &options[i];
		if (c->short_option != opt)
			continue;
		SETBIT(*selected_options, c->id);
		if (c->save)
			ret = c->save(c, c->help_value_name ? optarg : NULL, config);
		break;
	}
	return ret;
}

/**
 * Convert \p options to \p long_options accepted by `getopt_long` system call.
 */
static void convert_to_getopt_long_options(struct option *long_options,
					   const option_t *options, const int n) {
	int i;
	const option_t *c;
	for (i = 0; i < n; i++) {
		c = &options[i];
		long_options[i] = (struct option) {
			c->long_option,
			c->help_value_name ? required_argument : no_argument,
			NULL,
			c->short_option
		};
	}
	long_options[n] = (struct option) { 0, 0, NULL, 0 };
}

static void options_to_optstring(const option_t *options, const int n,
				 char *optstring) {
	int i, j = 0;
	optstring[j++] = ':'; /* Refer `getopt` manual for explanation */
	for (i = 0; i < n; i++) {
		optstring[j++] = options[i].short_option;
		if (options[i].help_value_name)
			optstring[j++] = ':';
	}
}

static void print_help(const option_t *options, const int n,
		       const char *project_prefix) {
	int i;
	const option_t *opt;
	printf(project_prefix);
	for (i = 0; i < n; i++) {
		opt = &options[i];
		printf("--%s -%c%s%s\n\t%s\n",
			opt->long_option,
			opt->short_option,
			opt->help_value_name ? " " : "",
			opt->help_value_name ? opt->help_value_name : "",
			opt->help_desc);
	}
	printf(POSIXLY_CORRECT_LONG_OPTIONS_MSG
	       "\nReport bugs to: <" AUTHOR_EMAIL ">.\n");
}

/**
 * Parse `argv` (of length \p argc), save results in \p allowed_options array
 * and in \p selected_options integer.
 */
int common_parse(int argc, char **argv, const option_t *allowed_options,
		 common_config_t *base_config, const int n) {
	char *optstring;
	int opt, ret = 0;
	uint32_t *selected_options = &base_config->selected_options;
#ifndef POSIXLY_CORRECT
	struct option *long_options = (struct option*)calloc(n + 1, sizeof(struct option));
	if (!long_options)
		ERR("calloc");
	convert_to_getopt_long_options(long_options, allowed_options, n);
#endif
	if (!(optstring = (char*)calloc(2 * n, sizeof(char))))
		ERR("calloc");
	options_to_optstring(allowed_options, n, optstring);
	while ((opt = GETOPT(argc, argv, optstring
#ifndef POSIXLY_CORRECT
	, long_options, NULL
#endif
	)) != -1) {
		if (opt == PARSER_MISSING_VALUE) {
			print_missing_value();
		} else if (opt == PARSER_UNRECOGNIZED_OPTION) {
			print_unrecognized_option();
		} if (save_option(allowed_options, opt, selected_options, base_config, n) < 0) {
			ret = -1;
			break;
		}
	}
	free(optstring);
#ifndef POSIXLY_CORRECT
	free(long_options);
#endif
	if (is_option_set(*selected_options, HELP_OPTION)) {
		print_help(allowed_options, n, base_config->help_prefix);
		ret = -1;
	} else if (is_option_set(*selected_options, VERSION_OPTION)) {
		print_version(base_config->project_name,
			      base_config->project_version);
		ret = -1;
	}
	return ret;
}

int port_save_fun(const struct option_t *option, const char *value, void *config) {
	int port = atoi(value);
	UNUSED(option);
	common_config_t *c = (common_config_t*)config;
	if (port < MIN_PORT_NUMBER || port > MAX_PORT_NUMBER) {
		printf("Port number is out of range. Port number must "
		       "be from range [%d,%d].\n", MIN_PORT_NUMBER, MAX_PORT_NUMBER);
		return -1;
	}
	c->port = port;
	return 0;
}

/*
 * See:
 * http://stackoverflow.com/questions/16245521/c99-inline-function-in-c-file/16245669#16245669
 */
int is_option_set(uint32_t selected_options, int opt);
