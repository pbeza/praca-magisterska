#include <libconfig.h>
#include <string.h>
#include <syslog.h>

#include "config_parser_file.h"

#include "config.h"

/**
 * @{ Accepted variables to be used in server's configuration file.
 */
#define CONFIG_FILE_PRIV_KEY_PASS	"PRIVATE_KEY_PASSWORD"

/** @} */

static void read_priv_key_pass(config_t *config, server_config_t *server_config) {
	const char *pass;
	base_config_t *base_config = BASE_CONFIG(server_config);
	security_config_t *security_config = SECURITY_CONFIG(server_config);

	if (is_option_set(base_config, PRIVATE_KEY_PASS_OPTION_ID))
		return;

	if (config_lookup_string(config, CONFIG_FILE_PRIV_KEY_PASS, &pass) == CONFIG_FALSE)
		syslog(LOG_WARNING, "Failed to read private key password from "
		       "config file");
	else
		syslog(LOG_DEBUG, "Password %s for private key read from "
		       "config file", pass);

	strncpy(security_config->private_key_pass, pass, MAX_PRIV_KEY_PASS_LEN);
}

static void server_read_config_from_file(config_t *config, server_config_t *server_config) {
	read_priv_key_pass(config, server_config);
}

int read_config_from_file(server_config_t *server_config) {
	int ret = -1;
	config_t config;
	base_config_t *base_config = BASE_CONFIG(server_config);
	const char *config_path = base_config->config_file_path;

	config_init(&config);

	if (config_read_file(&config, config_path) == CONFIG_FALSE) {
		syslog_config_file(&config, "config_read_file()");
		goto err_config;
	}

	if (common_read_config_from_file(&config, base_config) < 0) {
		syslog(LOG_ERR, "Failed to load common config from file");
		goto err_config;
	}

	server_read_config_from_file(&config, server_config);

	ret = 0;

err_config:
	config_destroy(&config);

	return ret;
}
