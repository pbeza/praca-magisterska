#include <assert.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "options.h"

/**
 * Parser return codes in case of missing option's value.
 */
#define PARSER_MISSING_VALUE		':'

/**
 * Parser return codes in case of unrecognized option.
 */
#define PARSER_UNRECOGNIZED_OPTION	'?'

/**
 * Common message for all warning parser's messages.
 */
#define CHECK_MANUAL_MSG		"Check manual for usage help."

/**
 * Print missing value message when some option needs an argument.
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
	exit(EXIT_FAILURE);
}

/**
 * Print unrecognized option value when option is not allowed.
 */
static inline void print_unrecognized_option() {
	fprintf(stderr,
#ifndef POSIXLY_CORRECT
	"Unrecognized option detected. " CHECK_MANUAL_MSG "\n"
#else
	"Unrecognized option -%c. " CHECK_MANUAL_MSG "\n", optopt
#endif
	);
	exit(EXIT_FAILURE);
}

/**
 * Call \ref option_t.save to parse and save option.
 */
static void save_option(const option_t* options, int opt, uint32_t* selected_options, void* config, const int n) {
	int i;
	const option_t* c;
	for (i = 0; i < n; i++) {
		c = &options[i];
		if (c->short_option != opt)
			continue;
		SETBIT(*selected_options, c->id);
		if (c->save)
			c->save(c, c->help_value_name ? optarg : NULL, config);
		break;
	}
}

/**
 * Fill array \p long_options with \p options in format required by `getopt_long`.
 */
static void add_getopt_long_options(struct option* long_options, const option_t* options, const int n) {
	int i;
	const option_t* c;
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
 * Parse `argv` and save results by calling \ref option_t.save with appropiate
 * pointer to \var option_t.
 */
void parse(int argc, char** argv, const char* optstring, const option_t* options, uint32_t* selected_options, void* config, const int n) {
	int opt;
#ifndef POSIXLY_CORRECT
	struct option long_options[n + 1];
	add_getopt_long_options(long_options, options, n);
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
		save_option(options, opt, selected_options, config, n);
	}
}
