/** \file
 * Universal `argv` options representation and basic parser used by both server
 * and client.
 */
#ifndef _COMMON_ARGV_PARSER_H
#define _COMMON_ARGV_PARSER_H

#include <stdint.h>

#include "common.h"
#include "config.h"

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
#define DESC_OPTION_DONT_DAEMONIZE	"Don't daemonize. By default application is daemonized. Both daemonized\n\t"\
					"and not daemonized application uses syslog for logging. Standard output\n\t"\
					"is used only for printing help message."
#define DESC_OPTION_PORT		"Server's listening port number. "\
					"Default is " STR(DEFAULT_SERVER_LISTENING_PORT) "."

/**
 * If user didn't specify listening port for server, this port is used.
 * \note See list of (un)assigned port numbers:
 * https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.txt
 */
#define DEFAULT_SERVER_LISTENING_PORT	4440

#ifdef POSIXLY_CORRECT
#define GETOPT getopt
#define OPTION(A, B, C, D, E, F)	{ A, B,    D, E, F }
#else
#define GETOPT getopt_long
#define OPTION(A, B, C, D, E, F)	{ A, B, C, D, E, F }
#endif

/**
 * Common initial config for both server and client.
 */
#define INIT_BASE_CONFIG		{\
					.project_name = PROJECT_NAME,\
					.project_version = PROJECT_VERSION,\
					.help_prefix = HELP_PREFIX,\
					.selected_options = 0,\
					.port = DEFAULT_SERVER_LISTENING_PORT\
					}

/**
 * Options' IDs.
 * \note Option ID is used as a bit index in `uint32_t` variable to mark active
 * options. Therefore IDs must be positive integers less than 32.
 * \warning Server's and client's IDs must be greater than common IDs.
 */
typedef enum {
	HELP_OPTION,
	VERSION_OPTION,
	PORT_OPTION,
	DONT_DAEMONIZE_OPTION
} option_code;

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
 * Parse `argv` and save parsed results in \p options and \p selected_options.
 */
int common_parse(int argc, char **argv, const option_t *options,
		 common_config_t *base_config, const int n);

int port_save_fun(const struct option_t *option, const char *value, void *config);

/**
 * Checks whether given \p option, represented by single bit, is set.
 */
inline int is_option_set(uint32_t selected_options, int option) {
	return IS_SETBIT(selected_options, option);
}

#endif
