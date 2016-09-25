/** \file
 * Implementation of server's `argv[]` parser.
 */
#include <getopt.h>
#include <string.h>
#include <unistd.h>

#include "config_parser_argv.h"

#include "security.h"

/**
 * @{ Short options' names.
 */
#define SHORT_OPTION_CERTIFICATE_PATH	'r'
#define SHORT_OPTION_PRIVATE_KEY_PATH	'k'
#define SHORT_OPTION_PRIVATE_KEY_PASS	's'

/**
 * @}
 * @{ Long options' names.
 */
#define LONG_OPTION_CERTIFICATE_PATH	"cert-path"
#define LONG_OPTION_PRIVATE_KEY_PATH	"privkey-path"
#define LONG_OPTION_PRIVATE_KEY_PASS	"privkey-pass"

/**
 * @}
 * @{ Options' values' names.
 */
#define CERTIFICATE_PATH_VALUE_NAME	"CERTIFICATE_PATH"
#define PRIVATE_KEY_PATH_VALUE_NAME	"PRIVATE_KEY_PATH"
#define PRIVATE_KEY_PASS_VALUE_NAME	"PRIVATE_KEY_PASSWORD"

/**
 * @}
 * @{ Options' description.
 */
#define DESC_OPTION_VERSION		"Print server's version number."
#define DESC_OPTION_CERTIFICATE_PATH	"Path to the file with server's certificate in PEM format. OpenSSL\n\t"\
					"recommends storing there whole chain of certificates. See notes\n\t"\
					"section in `SSL_CTX_use_certificate_chain_file` manual to learn\n\t"\
					"more."
#define DESC_OPTION_PRIVATE_KEY_PATH	"Path to the file with server's private key in PEM format."
#define DESC_OPTION_PRIVATE_KEY_PASS	"Password protecting private key. Warning: This option may be\n\t"\
					"useful only for debugging and may be removed or limited to\n\t"\
					"debug compilation in the future. Specifying password as a\n\t"\
					"command line option is NOT recommended since everyone can see\n\t"\
					"this password (using `ps` command). Use configuration file instead."

/**
 * @}
 * @{ Server specific options defined as as \a option_t structures.
 */
#define CERTIFICATE_PATH_OPTION		OPTION(CERTIFICATE_PATH_OPTION_ID,\
					       SHORT_OPTION_CERTIFICATE_PATH,\
					       LONG_OPTION_CERTIFICATE_PATH,\
					       DESC_OPTION_CERTIFICATE_PATH,\
					       CERTIFICATE_PATH_VALUE_NAME,\
					       cert_path_save_cb)
#define PRIVATE_KEY_PATH_OPTION		OPTION(PRIVATE_KEY_PATH_OPTION_ID,\
					       SHORT_OPTION_PRIVATE_KEY_PATH,\
					       LONG_OPTION_PRIVATE_KEY_PATH,\
					       DESC_OPTION_PRIVATE_KEY_PATH,\
					       PRIVATE_KEY_PATH_VALUE_NAME,\
					       priv_key_path_save_cb)
#define PRIVATE_KEY_PASS_OPTION		OPTION(PRIVATE_KEY_PASS_OPTION_ID,\
					       SHORT_OPTION_PRIVATE_KEY_PASS,\
					       LONG_OPTION_PRIVATE_KEY_PASS,\
					       DESC_OPTION_PRIVATE_KEY_PASS,\
					       PRIVATE_KEY_PASS_VALUE_NAME,\
					       priv_key_pass_save_cb)
#define SET_OF_SERVER_OPTIONS		CERTIFICATE_PATH_OPTION,\
					PRIVATE_KEY_PATH_OPTION,\
					PRIVATE_KEY_PASS_OPTION

/**
 * @}
 * Function callback saving server's certificate path in server's configuration.
 */
static int cert_path_save_cb(const option_t *option, const char *value, void *config) {
	server_config_t *c = (server_config_t*)config;
	security_config_t *s = SECURITY_CONFIG(c);

	if (access(value, F_OK | R_OK)) {
		print_no_file_msg_argv(option->short_option, option->long_option, value);
		return -1;
	}

	strncpy(s->certificate_path, value, PATH_MAX_LEN);

	return 0;
}

/**
 * Function callback saving server's private key path in server's configuration.
 */
static int priv_key_path_save_cb(const option_t *option, const char *value, void *config) {
	server_config_t *c = (server_config_t*)config;
	security_config_t *s = SECURITY_CONFIG(c);

	if (access(value, F_OK | R_OK)) {
		print_no_file_msg_argv(option->short_option, option->long_option, value);
		return -1;
	}

	strncpy(s->private_key_path, value, PATH_MAX_LEN);

	return 0;
}

/**
 * Function callback saving server's private key password in server's configuration.
 * \warning Note that password for PEM private key file preferably should be
 * stored in server's configuration file.
 */
static int priv_key_pass_save_cb(const option_t *option, const char *value, void *config) {
	server_config_t *c = (server_config_t*)config;
	security_config_t *s = SECURITY_CONFIG(c);
	UNUSED(option);
	strncpy(s->private_key_pass, value, MAX_PRIV_KEY_PASS_LEN);
	return 0;
}

int read_config_from_argv(int argc, char **argv, server_config_t *config) {
	const option_t allowed_options[] = {
		SET_OF_COMMON_OPTIONS,
		SET_OF_SERVER_OPTIONS
	};
	const int n = ARRAY_LENGTH(allowed_options);
	return common_read_config_from_argv(argc, argv, allowed_options, (void*)config, n);
}
