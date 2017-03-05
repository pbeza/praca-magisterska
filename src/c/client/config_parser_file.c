#include <libconfig.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>

#include "config_parser_file.h"

#include "config.h"

static int client_read_config_from_file(config_t *config, client_config_t *client_config) {
	base_config_t *base_config = BASE_CONFIG(client_config);
	security_config_t *security_config = SECURITY_CONFIG(client_config);

	if (read_file_path_from_conf(config,
				     base_config,
				     TRUSTED_CERT_FILE_OPTION_ID,
				     CONFIG_FILE_TRUSTED_CERT_FILE,
				     security_config->trusted_cert_file,
				     0) < 0) {
		syslog(LOG_ERR, "Failed to read trusted certificate file path "
		       "from configuration file");
		return -1;
	}

	if (read_dir_path_from_conf(config,
				    base_config,
				    TRUSTED_CERT_DIR_OPTION_ID,
				    CONFIG_FILE_TRUSTED_CERT_DIR,
				    security_config->trusted_cert_dir,
				    0) < 0) {
		syslog(LOG_ERR, "Error reading trusted certificate directory "
		       "from configuration file");
		return -1;
	}

	return 0;
}

int read_config_from_file(client_config_t *client_config) {
	int ret = -1;
	config_t config;
	base_config_t *base_config = BASE_CONFIG(client_config);
	const char *config_path = base_config->config_file_path;

	config_init(&config);

	if (config_read_file(&config, config_path) == CONFIG_FALSE) {
		syslog_config_file(&config, "config_read_file()");
		goto err_config;
	}

	if (common_read_config_from_file(&config, base_config) < 0) {
		syslog(LOG_ERR, "Failed to load common configuration from file");
		goto err_config;
	}

	if (client_read_config_from_file(&config, client_config) < 0) {
		syslog(LOG_ERR, "Failed to load client configuration from file");
		goto err_config;
	}

	ret = 0;

err_config:
	config_destroy(&config);

	return ret;
}
