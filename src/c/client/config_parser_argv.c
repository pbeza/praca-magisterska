/** \file
 * Implementation of client's `argv[]` parser.
 */
#include <arpa/inet.h>
#include <errno.h>
#include <getopt.h>
#include <string.h>
#include <unistd.h>

#include "config_parser_argv.h"

/**
 * @{ Short options' names.
 */
#define SHORT_OPTION_TRUSTED_CERT_FILE	't'
#define SHORT_OPTION_TRUSTED_CERT_DIR	'u'

/**
 * @}
 * @{ Long options' names.
 */
#define LONG_OPTION_TRUSTED_CERT_FILE	"trusted-cert"
#define LONG_OPTION_TRUSTED_CERT_DIR	"trusted-cert-dir"

/**
 * @}
 * @{ Options' values' names.
 */
#define TRUSTED_CERT_FILE_VALUE_NAME	"TRUSTED_CERT_FILE"
#define TRUSTED_CERT_DIR_VALUE_NAME	"TRUSTED_CERT_DIR"

/**
 * @}
 * @{ Options' description.
 */
#define DESC_OPTION_VERSION		"Print client's version number."
#define DESC_OPTION_TRUSTED_CERT_FILE	"Path to server's trusted CA certificate in PEM format."
#define DESC_OPTION_TRUSTED_CERT_DIR	"Path to directory with CA trusted certificates in PEM format."

/**
 * @}
 * @{ Client specific options defined as as \a option_t structures.
 */
#define TRUSTED_CERT_FILE_OPTION	OPTION(TRUSTED_CERT_FILE_OPTION_ID,\
					       SHORT_OPTION_TRUSTED_CERT_FILE,\
					       LONG_OPTION_TRUSTED_CERT_FILE,\
					       DESC_OPTION_TRUSTED_CERT_FILE,\
					       TRUSTED_CERT_FILE_VALUE_NAME,\
					       trusted_cert_file_save_cb)
#define TRUSTED_CERT_DIR_OPTION		OPTION(TRUSTED_CERT_DIR_OPTION_ID,\
					       SHORT_OPTION_TRUSTED_CERT_DIR,\
					       LONG_OPTION_TRUSTED_CERT_DIR,\
					       DESC_OPTION_TRUSTED_CERT_DIR,\
					       TRUSTED_CERT_DIR_VALUE_NAME,\
					       trusted_cert_dir_save_cb)

/**
 * @}
 * Function callback saving trusted certificate in client's security configuration.
 */
static int trusted_cert_file_save_cb(const option_t *option, const char *value, void *config) {
	client_config_t *c = (client_config_t*)config;
	security_config_t *s = SECURITY_CONFIG(c);

	if (access(value, F_OK | R_OK)) {
		print_no_file_msg_argv(option->short_option, option->long_option, value);
		return -1;
	}

	strncpy(s->trusted_cert_file, value, PATH_MAX_LEN);

	return 0;
}

/**
 * Function callback saving directory with trusted certificates in client's
 * security configuration.
 */
static int trusted_cert_dir_save_cb(const option_t *option, const char *value, void *config) {
	client_config_t *c = (client_config_t*)config;
	security_config_t *s = SECURITY_CONFIG(c);

	if (access(value, F_OK | R_OK)) {
		print_no_file_msg_argv(option->short_option, option->long_option, value);
		return -1;
	}

	strncpy(s->trusted_cert_dir, value, PATH_MAX_LEN);

	return 0;
}

static int read_srv_addr_from_argv(int argc, char **argv, client_config_t *config) {
	int d = argc - optind;
	char *last = argv[argc - 1];

	if (d == 1) {
		config->serv_addr_str = last;
	} else if (d == 0 && !(strlen(last) == 2 && !strncmp(last, "--", 2))) {
		fprintf(stderr, "Missing server's address. See --" LONG_OPTION_HELP ".\n");
		return -1;
	} else {
		fprintf(stderr, "Unexpected options. See --" LONG_OPTION_HELP ".\n");
		return -1;
	}

	return 0;
}

int read_config_from_argv(int argc, char **argv, client_config_t *config) {
	const option_t allowed_options[] = {
		SET_OF_COMMON_OPTIONS,
		TRUSTED_CERT_FILE_OPTION,
		TRUSTED_CERT_DIR_OPTION
	};
	const int n = ARRAY_LENGTH(allowed_options);
	return common_read_config_from_argv(argc, argv, allowed_options, (void*)config, n) < 0 ?
		-1 : read_srv_addr_from_argv(argc, argv, config);
}
