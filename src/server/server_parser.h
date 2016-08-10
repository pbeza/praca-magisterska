/** \file
 * Server's `argv` parser.
 */

#ifndef _SERVER_PARSER_H
#define _SERVER_PARSER_H

#include "common/utils/options.h"
#include "server_config.h"

#ifdef POSIXLY_CORRECT
#define POSIXLY_CORRECT_MSG	"Note: Long options are not supported in this build.\n"
#else
#define POSIXLY_CORRECT_MSG
#endif

/**
 * Beginning of the help section.
 */
#define HELP_PREFIX		"Usage: " PROJECT_NAME " [ options ]\n\n"\
				"Starts server providing application's packages for clients.\n\n"\
				"Options:\n\n"

/**
 * Ending of the help section.
 */
#define HELP_POSTFIX		POSIXLY_CORRECT_MSG "\nReport bugs to: <patryk.beza@gmail.com>.\n"

/**
 * Options' arguments IDs.
 * \note Option ID is used as a bit index in `uint32_t` variable to mark
 * active options. Therefore IDs must be positive integers less than 32.
 */
typedef enum {
	HELP_OPTION,
	VERSION_OPTION,
	PORT_OPTION
} option_code;

/*
 * Short options' names.
 */

#define SHORT_OPTION_HELP	'h'
#define SHORT_OPTION_VERSION	'v'
#define SHORT_OPTION_PORT	'p'

/*
 * Long options' names.
 */

#define LONG_OPTION_HELP	"help"
#define LONG_OPTION_VERSION	"version"
#define LONG_OPTION_PORT	"port"

/*
 * Options' values' names.
 */

#define OPTION_VALUE_NAME	"PORT_NUMBER"

/*
 * Options' description.
 */

#define DESC_OPTION_HELP	"Print this help message."
#define DESC_OPTION_VERSION	"Print server's version number."
#define DESC_OPTION_PORT	"Port number for clients' listening."

/**
 * See `getopt` manual for optstring prefix meaning.
 */
#define OPTSTRING_PREFIX	":"

/**
 * Options string for `getopt`.
 */
#define GETOPT_STRING		OPTSTRING_PREFIX "hvp:"

/**
 * Add application's allowed options, parse `argv` and save result to \p config.
 * Returns negative integer if application should exit.
 */
int parse_argv(int argc, char** argv, config_t* config);

#endif
