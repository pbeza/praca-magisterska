/** \file
 * Universal `argv[]` options representation and basic parser used by both
 * server and client.
 */
#ifndef _COMMON_CONFIG_PARSER_H
#define _COMMON_CONFIG_PARSER_H

#include <stdint.h>

#include "config.h"

/**
 * @{ Short options' names.
 * \warning Make sure that neither client nor server use the same character.
 */
#define SHORT_OPTION_HELP		'h'
#define SHORT_OPTION_VERSION		'v'
#define SHORT_OPTION_PORT		'p'
#define SHORT_OPTION_DONT_DAEMONIZE	'd'
#define SHORT_OPTION_CONFIG_FILE	'c'

/**
 * @}
 * @{ Long options' names.
 */
#define LONG_OPTION_HELP		"help"
#define LONG_OPTION_VERSION		"version"
#define LONG_OPTION_PORT		"port"
#define LONG_OPTION_DONT_DAEMONIZE	"nodaemon"
#define LONG_OPTION_CONFIG_FILE		"config-file"

/**
 * @}
 * @{ Options' values' names.
 */
#define PORT_OPTION_VALUE_NAME		"PORT_NUMBER"
#define CONFIG_FILE_VALUE_NAME		"CONFIGURATION_FILE"

/**
 * @}
 * @{ Options' description.
 */
#define DESC_OPTION_HELP		"Print this help message."
#define DESC_OPTION_PORT		"Server's listening port number. "\
					"Default is " STR(DEFAULT_SERVER_LISTENING_PORT) "."
#define DESC_OPTION_DONT_DAEMONIZE	"Don't daemonize. By default application is daemonized. Regardless of\n\t"\
					"whether application is daemonized or not, it uses syslog for logging.\n\t"\
					"Standard output is used only for printing help message and argv[]\n\t"\
					"parser error messages."
#define DESC_OPTION_CONFIG_FILE		"Path to configuration file. If not provided, default path will be used." 

/**
 * @}
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
					       port_save_cb)
#define DONT_DAEMONIZE_OPTION		OPTION(DONT_DAEMONIZE_OPTION_ID,\
					       SHORT_OPTION_DONT_DAEMONIZE,\
					       LONG_OPTION_DONT_DAEMONIZE,\
					       DESC_OPTION_DONT_DAEMONIZE,\
					       NULL,\
					       NULL)
#define CONFIG_FILE_OPTION		OPTION(CONFIG_FILE_ID,\
					       SHORT_OPTION_CONFIG_FILE,\
					       LONG_OPTION_CONFIG_FILE,\
					       DESC_OPTION_CONFIG_FILE,\
					       CONFIG_FILE_VALUE_NAME,\
					       config_file_save_cb)
#define SET_OF_COMMON_OPTIONS		HELP_OPTION,\
					VERSION_OPTION,\
					PORT_OPTION,\
					DONT_DAEMONIZE_OPTION,\
					CONFIG_FILE_OPTION

/**
 * @}
 * Parse `argv[]` and save parsed results in \p options and \p selected_options.
 */
int common_read_config_from_argv(int argc, char **argv, const option_t *options, void *config, int n);

int port_save_cb(const option_t *option, const char *value, void *config);

int config_file_save_cb(const option_t *option, const char *value, void *config);

void print_no_file_msg_argv(char short_option, const char *long_option, const char *file);

void print_no_dir_msg_argv(char short_option, const char *long_option, const char *file);

#endif
