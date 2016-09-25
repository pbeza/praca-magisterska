#include <libconfig.h>
#include <string.h>
#include <syslog.h>

#include "config_parser_file.h"

#include "config.h"

static int read_priv_key_pass(const config_t *config, server_config_t *server_config) {
	const char *pass;
	base_config_t *base_config = BASE_CONFIG(server_config);
	security_config_t *security_config = SECURITY_CONFIG(server_config);

	if (is_option_set(base_config, PRIVATE_KEY_PASS_OPTION_ID))
		return 0;

	if (config_lookup_string(config, CONFIG_FILE_PRIV_KEY_PASS, &pass) == CONFIG_FALSE) {
		fprintf(stderr, "Error parsing configuration file. Required "
			"option '%s' not provided.\n", CONFIG_FILE_PRIV_KEY_PASS);
		return -1;
	}

	if (strlen(pass) > MAX_PRIV_KEY_PASS_LEN) {
		fprintf(stderr, "Error parsing configuration file. Password "
			"protecting private key is too long.\n");
		return -1;
	}

	strncpy(security_config->private_key_pass, pass, MAX_PRIV_KEY_PASS_LEN);

	syslog(LOG_INFO, "Password for private key successfully loaded from "
	       "configuration file");

	return 0;
}

static int server_read_config_from_file(const config_t *config, server_config_t *server_config) {
	base_config_t *base_config = BASE_CONFIG(server_config);
	security_config_t *security_config = SECURITY_CONFIG(server_config);

	if (read_priv_key_pass(config, server_config) < 0) {
		syslog(LOG_ERR, "Failed to read password from configuration "
		       "file protecting server's private key");
		return -1;
	}

	if (read_path_from_conf(config, base_config, PRIVATE_KEY_PATH_OPTION_ID,
				CONFIG_FILE_PRIV_KEY_PATH,
				security_config->private_key_path, 1) < 0) {
		syslog(LOG_ERR, "Failed to read private key path from "
		       "configuration file");
		return -1;
	}

	if (read_path_from_conf(config, base_config, CERTIFICATE_PATH_OPTION_ID,
				CONFIG_FILE_CERTIFICATE_PATH,
				security_config->certificate_path, 1) < 0) {
		syslog(LOG_INFO, "Provide path to server's private key by "
		       "assigning path to `%s` variable in configuration file",
		       CONFIG_FILE_PRIV_KEY_PATH);
		return -1;
	}

	return 0;
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

	if (server_read_config_from_file(&config, server_config) < 0) {
		syslog(LOG_ERR, "Failed to load client configuration from file");
		goto err_config;
	}

	ret = 0;

err_config:
	config_destroy(&config);

	return ret;
}
