#include <libconfig.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>

#include "config_parser_file.h"

#include "config.h"

/**
 * @{ Accepted variables to be used in client's configuration file.
 */
#define CONFIG_FILE_TRUSTED_CERT_FILE	"CA_CERT_FILE"
#define CONFIG_FILE_TRUSTED_CERT_DIR	"CA_CERT_DIR"

/** @} */

static int read_file_from_conf(config_t *config,
			       client_config_t *client_config,
			       client_option_code option_id,
			       const char *config_var_path,
			       char *config_save_path) {
	const char *path;
	base_config_t *base_config = BASE_CONFIG(client_config);

	if (is_option_set(base_config, option_id))
		return 0;

	if (config_lookup_string(config, config_var_path, &path) == CONFIG_FALSE) {
		syslog(LOG_DEBUG, "Option '%s' not set in configuration file. "
		       "Default value will be used", config_var_path);
		return 0;
	}

	if (access(path, F_OK | R_OK)) {
		print_no_file_msg_conf(path);
		return -1;
	}

	strncpy(config_save_path, path, PATH_MAX_LEN);

	syslog(LOG_DEBUG, "Path '%s' loaded from config file", path);

	return 0;
}

static int read_trusted_cert_file(config_t *config, client_config_t *client_config) {
	security_config_t *security_config = SECURITY_CONFIG(client_config);
	if (read_file_from_conf(config,
				client_config,
				TRUSTED_CERT_FILE_OPTION_ID,
				CONFIG_FILE_TRUSTED_CERT_FILE,
				security_config->trusted_cert_file) < 0) {
		syslog(LOG_WARNING, "Failed to read trusted certificate file "
		       "from config file");
		return -1;
	}

	return 0;
}

static int read_trusted_cert_dir(config_t *config, client_config_t *client_config) {
	security_config_t *security_config = SECURITY_CONFIG(client_config);
	if (read_file_from_conf(config,
				client_config,
				TRUSTED_CERT_DIR_OPTION_ID,
				CONFIG_FILE_TRUSTED_CERT_DIR,
				security_config->trusted_cert_dir) < 0) {
		syslog(LOG_WARNING, "Failed to read trusted certificate directory "
		       "from config file");
		return -1;
	}

	return 0;
}

static int client_read_config_from_file(config_t *config, client_config_t *client_config) {
	if (read_trusted_cert_file(config, client_config) < 0)
		return -1;

	if (read_trusted_cert_dir(config, client_config) < 0)
		return -1;

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
		syslog(LOG_ERR, "Failed to load common config from file");
		goto err_config;
	}

	if (client_read_config_from_file(&config, client_config) < 0) {
		syslog(LOG_ERR, "Failed to load client config from file");
		goto err_config;
	}

	ret = 0;

err_config:
	config_destroy(&config);

	return ret;
}
