/** \file
 * Server's `argv` parser.
 */
#ifndef _SERVER_PARSER_H
#define _SERVER_PARSER_H

#include "common/options.h"
#include "config.h"

#ifdef POSIXLY_CORRECT
#define POSIXLY_CORRECT_MSG		"Note: Long options are not supported in this build.\n"
#else
#define POSIXLY_CORRECT_MSG
#endif

/**
 * Beginning of the help section.
 */
#define HELP_PREFIX			"Usage: " PROJECT_NAME " [ options ]\n\n"\
					"Starts server providing application's packages for clients.\n\n"\
					"Options:\n\n"

/**
 * Ending of the help section.
 */
#define HELP_POSTFIX			POSIXLY_CORRECT_MSG "\nReport bugs to: <patryk.beza@gmail.com>.\n"

/**
 * Options' arguments IDs.
 * \note Option ID is used as a bit index in `uint32_t` variable to mark
 * active options. Therefore IDs must be positive integers less than 32.
 */
typedef enum {
	HELP_OPTION,
	VERSION_OPTION,
	PORT_OPTION,
	DONT_DAEMONIZE_OPTION
} option_code;

/*
 * Short options' names.
 */

#define SHORT_OPTION_HELP		'h'
#define SHORT_OPTION_VERSION		'v'
#define SHORT_OPTION_PORT		'p'
#define SHORT_OPTION_DONT_DAEMONIZE	'd'

/*
 * Long options' names.
 */

#define LONG_OPTION_HELP		"help"
#define LONG_OPTION_VERSION		"version"
#define LONG_OPTION_PORT		"port"
#define LONG_OPTION_DONT_DAEMONIZE	"nodaemon"

/*
 * Options' values' names.
 */

#define OPTION_VALUE_NAME		"PORT_NUMBER"

/*
 * Options' description.
 */

#define DESC_OPTION_HELP		"Print this help message."
#define DESC_OPTION_VERSION		"Print server's version number."
#define DESC_OPTION_PORT		"Port number for clients' listening."
#define DESC_OPTION_DONT_DAEMONIZE	"Don't daemonize server. "\
					"Server is daemonized by default"

/**
 * See `getopt` manual for optstring prefix meaning.
 */
#define OPTSTRING_PREFIX	":"

/**
 * Options string for `getopt`.
 */
#define GETOPT_STRING		OPTSTRING_PREFIX "hvp:d"

/**
 * Application configuration - both precompiled and parsed from `argv`.
 */
typedef struct config_t {
	/**
	 * Selected runtime options are represented by single bits set to 1.
	 */
	uint32_t selected_options;
	/**
	 * Server's listening port.
	 */
	uint16_t port;
} config_t;

/**
 * Precompiled  application configuration ie. configuration before parsing `argv`.
 */
static const config_t INIT_CONFIG = {
	.selected_options = 0,
	.port = DEFAULT_SERVER_LISTENING_PORT
};

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse_argv(int argc, char **argv, config_t *config);

inline int is_option_set(const config_t *config, int opt) {
	return IS_SETBIT(config->selected_options, opt);
}

#endif
