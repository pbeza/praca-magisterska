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
 * \warning Make sure that neither server nor client use the same character.
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
#define PORT_OPTION_VALUE_NAME		"PORT_NUMBER"

/**
 * @{ Options' description.
 */
#define DESC_OPTION_HELP		"Print this help message."
#define DESC_OPTION_PORT		"Server's listening port number. "\
					"Default is " STR(DEFAULT_SERVER_LISTENING_PORT) "."
#define DESC_OPTION_DONT_DAEMONIZE	"Don't daemonize. By default application is daemonized. Regardless of\n\t"\
					"whether application is daemonized or not, it uses syslog for logging.\n\t"\
					"Standard output is used only for printing help message and `argv`\n\t"\
					"parser error messages."

/**
 * @}
 * If user didn't specify listening port for server, this port is used.
 * \note See list of (un)assigned port numbers:
 * https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.txt
 */
#define DEFAULT_SERVER_LISTENING_PORT	4440

/**
 * Macro to create \a option_t structure, which size depends on
 * `POSIXLY_CORRECT` compilation time constant.
 */
#ifdef POSIXLY_CORRECT
#define GETOPT getopt
#define OPTION(A, B, C, D, E, F)	{ A, B,    D, E, F }
#else
#define GETOPT getopt_long
#define OPTION(A, B, C, D, E, F)	{ A, B, C, D, E, F }
#endif

/**
 * @{ Common options defined as as \a option_t structures.
 */
#define HELP_OPTION			OPTION(HELP_OPTION_ID,\
					       SHORT_OPTION_HELP,\
					       LONG_OPTION_HELP,\
					       DESC_OPTION_HELP,\
					       NULL,\
					       NULL)
#define VERSION_OPTION			OPTION(VERSION_OPTION_ID,\
					       SHORT_OPTION_VERSION,\
					       LONG_OPTION_VERSION,\
					       DESC_OPTION_VERSION,\
					       NULL,\
					       NULL)
#define PORT_OPTION			OPTION(PORT_OPTION_ID,\
					       SHORT_OPTION_PORT,\
					       LONG_OPTION_PORT,\
					       DESC_OPTION_PORT,\
					       PORT_OPTION_VALUE_NAME,\
					       port_save_fun)
#define DONT_DAEMONIZE_OPTION		OPTION(DONT_DAEMONIZE_OPTION_ID,\
					       SHORT_OPTION_DONT_DAEMONIZE,\
					       LONG_OPTION_DONT_DAEMONIZE,\
					       DESC_OPTION_DONT_DAEMONIZE,\
					       NULL,\
					       NULL)
#define SET_OF_COMMON_OPTIONS		HELP_OPTION,\
					VERSION_OPTION,\
					PORT_OPTION,\
					DONT_DAEMONIZE_OPTION

/**
 * @}
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
	HELP_OPTION_ID,
	VERSION_OPTION_ID,
	PORT_OPTION_ID,
	DONT_DAEMONIZE_OPTION_ID,
	__LAST_COMMON_OPTION_ID /* for reference in server's and client's parsers */
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
		 void *config, const int n);

int port_save_fun(const struct option_t *option, const char *value, void *config);

/**
 * Checks whether given \p option, represented by single bit, is set.
 */
inline int is_option_set(const common_config_t *common_config, int option) {
	return IS_SETBIT(common_config->selected_options, option);
}

inline int is_dont_daemonize_set(const common_config_t *common_config) {
	return is_option_set(common_config, DONT_DAEMONIZE_OPTION_ID);
}

inline int is_print_help_set(const common_config_t *common_config) {
	return is_option_set(common_config, HELP_OPTION_ID);
}

inline int is_print_version_set(const common_config_t *common_config) {
	return is_option_set(common_config, VERSION_OPTION_ID);
}

#endif
