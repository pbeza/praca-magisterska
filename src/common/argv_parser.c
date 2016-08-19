#include <assert.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "argv_parser.h"

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
 * Print missing value message when some option requires an argument and exit.
 */
static inline void print_missing_value() {
/** \c getopt_long() doesn't store error in optopt in opposite to \c getopt() ;( */
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
static inline void print_unrecognized_option() {
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

/**
 * For given short option \p opt, find \ref option_t.save action in \p options
 * array (of length \p n) and execute it. Set \ref option_t.id-th bit in
 * \p selected_options integer, to indicate that this option is active.
 */
static int save_option(const option_t *options, int opt, uint32_t *selected_options, void *config, const int n) {
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
static void convert_to_getopt_long_options(struct option *long_options, const option_t *options, const int n) {
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

/**
 * Parse `argv` (of length \p argc), save results in \p options array and in
 * \p selected_options integer.
 */
int parse(int argc, char **argv, const char *optstring, const option_t *options, uint32_t *selected_options, void *config, const int n) {
	int opt, ret;
#ifndef POSIXLY_CORRECT
	struct option long_options[n + 1];
	convert_to_getopt_long_options(long_options, options, n);
#endif
	while ((opt = GETOPT(argc, argv, optstring
#ifndef POSIXLY_CORRECT
	, long_options, NULL
#endif
	)) != -1) {
		if (opt == PARSER_MISSING_VALUE)
			print_missing_value();
		else if (opt == PARSER_UNRECOGNIZED_OPTION)
			print_unrecognized_option();
		ret = save_option(options, opt, selected_options, config, n);
		if (ret < 0)
			return ret;
	}
	return 0;
}

void print_help(const option_t *options, const int n, const char *help_prefix, const char *help_postfix) {
	int i;
	const option_t *opt;
	printf(help_prefix);
	for (i = 0; i < n; i++) {
		opt = &options[i];
		printf("--%s -%c%s%s\n\t%s\n",
			opt->long_option,
			(char)opt->short_option,
			opt->help_value_name ? " " : "",
			opt->help_value_name ? opt->help_value_name : "",
			opt->help_desc);
	}
	printf(help_postfix);
}

/*
 * See:
 * http://stackoverflow.com/questions/16245521/c99-inline-function-in-c-file/16245669#16245669
 */
int is_option_set(uint32_t selected_options, int opt);
