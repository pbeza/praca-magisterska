/** \file
 * Universal `argv` options representation and basic parser used by both server
 * and client.
 */
#ifndef _ARGV_PARSER_H
#define _ARGV_PARSER_H

#include <stdint.h>

#include "common.h"
#include "config.h"

#ifdef POSIXLY_CORRECT
#define GETOPT getopt
#define OPTION(A, B, C, D, E, F)	{ A, B,    D, E, F }
#else
#define GETOPT getopt_long
#define OPTION(A, B, C, D, E, F)	{ A, B, C, D, E, F }
#endif

/**
 * Represents single runtime option read from `argv`.
 */
typedef struct option_t {
	/**
	 * Unique ID enumerated from 0.
	 * \note *Rationale* This ID can be used as a index in array of options.
	 */
	const uint8_t id;
	/**
	  * Single character representing short option for `getopt()`.
	  */
	char short_option;
#ifndef POSIXLY_CORRECT
	/**
	 * String representing long option for `getopt_long()`.
	 * \note This variable is not defined if `POSIXLY_CORRECT` is defined.
	 */
	const char *long_option;
#endif
	/**
	 * Help description displayed when `--help` is present.
	 */
	const char *help_desc;
	/**
	 * Parameter's value named displayed in `--help`.
	 * If parameter has no value use `NULL`.
	 */
	const char *help_value_name;
	/**
	 * Function handler called when this option is present in `argv[]`.
	 * If this function pointer is `NULL`, no function is called.
	 */
	int (*save)(const struct option_t *option, const char *value, void *config);
} option_t;

/**
 * Options' IDs.
 * \note Option ID is used as a bit index in `uint32_t` variable to mark active
 * options. Therefore IDs must be positive integers less than 32.
 */
typedef enum {
	HELP_OPTION,
	VERSION_OPTION,
	PORT_OPTION,
	DONT_DAEMONIZE_OPTION
} option_code;

/**
 * @{ Short options' names.
 */
#define SHORT_OPTION_HELP		'h'
#define SHORT_OPTION_VERSION		'v'
#define SHORT_OPTION_PORT		'p'
#define SHORT_OPTION_DONT_DAEMONIZE	'd'

/**
 * @}
 * @{ Long options' names.
 */
#define LONG_OPTION_HELP		"help"
#define LONG_OPTION_VERSION		"version"
#define LONG_OPTION_PORT		"port"
#define LONG_OPTION_DONT_DAEMONIZE	"nodaemon"

/**
 * @}
 * Options' values' names.
 */
#define OPTION_VALUE_NAME		"PORT_NUMBER"

/**
 * Options' description.
 */
#define DESC_OPTION_HELP		"Print this help message."
#define DESC_OPTION_DONT_DAEMONIZE	"Don't daemonize. "\
					"By default application is daemonized."

/**
 * If user didn't specify listening port for server, this port is used.
 * \note See list of (un)assigned port numbers:
 * https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.txt
 */
#define DEFAULT_SERVER_LISTENING_PORT	4440

/**
 * Minimum allowed port number accepted by both server's and client's parser.
 */
#define MIN_PORT_NUMBER			1025

/**
 * Maximum allowed port number accepted by both server's and client's parser.
 */
#define MAX_PORT_NUMBER			65535

/**
 * Parse `argv` and save parsed results in \p options and \p selected_options.
 */
int parse(int argc, char **argv, const char *optstring, const option_t *options, uint32_t *selected_options, void *config, const int n);

void print_help(const option_t *options, const int n, const char *help_prefix, const char *help_postfix);

/**
 * Checks whether given \p option, represented by single bit, is set.
 */
inline int is_option_set(uint32_t selected_options, int option) {
	return IS_SETBIT(selected_options, option);
}

#endif
