#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "packages_manager.h"

#include "common/misc.h"

#define CHANGE_CWD_TO_PKG_CACHE_DIR_CMD	"cd '%s'"
#define APT_PKG_DOWNLOAD_CMD		"apt-get download"
#define PKG_DOWNLOAD_CMD_RESIZE_FACTOR	2
#define MIN_PKG_DOWNLOAD_CMD_CHAR_LEN	4096
#define MAX_PKG_NAME_LEN		4096
/*#define PKG_CACHE_DIR			"/var/cache/apt/archives"*/

static int append_pkg_list(const char *config_set_absolute_path,
			   char **download_cmd,
			   size_t *cmd_buf_len) {
	int ret = 0,
	    pkg_count;
	FILE *file;
	char pkg_name[MAX_PKG_NAME_LEN];
	size_t cmd_len = strlen(*download_cmd);
	char *fgets_res;

	do {
		file = fopen(config_set_absolute_path, "r");
	} while (!file && errno == EINTR);

	if (!file) {
		syslog(LOG_ERR, "Failed to open config set file %s", config_set_absolute_path);
		return -1;
	}

	for (pkg_count = 0 ;; pkg_count++) {
		do {
			errno = 0;
		} while (!(fgets_res = fgets(pkg_name, sizeof(pkg_name), file)) && errno == EINTR);

		if (errno) {
			syslog_errno("fgets() failed reading config set");
			ret = -1;
			break;
		} else if (!fgets_res) {
			syslog(LOG_DEBUG, "%d packages read from config set `%s`",
			       pkg_count, config_set_absolute_path);
			break;
		}

		const size_t n = strcspn(pkg_name, "\n"),
			     k = cmd_len + n + 2;

		/* If we ran out of free space for command - realloc().
		 * +2 is for 1 space character and 1 trailing null byte.
		 */

		if (k >= *cmd_buf_len) {
			const size_t new_buf_len = MAX(k, PKG_DOWNLOAD_CMD_RESIZE_FACTOR * *cmd_buf_len);
			char *tmp = realloc(*download_cmd, new_buf_len);
			if (!tmp) {
				syslog_errno("realloc() failed for config set");
				ret = -1;
				break;
			}
			*cmd_buf_len = new_buf_len;
			*download_cmd = tmp;
		}
		strncpy(*download_cmd + cmd_len, " ", 1);
		strncpy(*download_cmd + cmd_len + 1, pkg_name, n);
		cmd_len += n + 1; /* +1 for space character */
		syslog(LOG_DEBUG, *download_cmd);
	}

	if (TEMP_FAILURE_RETRY(fclose(file)) < 0) {
		syslog_errno("Failed to close() config set file");
		return -1;
	}

	return ret;
}

int download_missing_packages(const server_config_t *srv_conf,
			      const upgrade_request_t *req) {
	/* http://stackoverflow.com/questions/13756800/how-to-download-all-dependencies-and-packages-to-directory
	 * http://superuser.com/questions/876727/how-to-download-deb-package-and-all-dependencies
	 */

	int ret = 0;
	size_t cmd_buf_len = MIN_PKG_DOWNLOAD_CMD_CHAR_LEN;
	char *download_cmd = malloc(cmd_buf_len);

	if (!download_cmd) {
		syslog_errno("malloc() for download command");
		return -1;
	}

	const char *cmd_prefix = CHANGE_CWD_TO_PKG_CACHE_DIR_CMD " && " APT_PKG_DOWNLOAD_CMD;
	snprintf(download_cmd, cmd_buf_len, cmd_prefix, srv_conf->pkg_cache_dir);

	if (append_pkg_list(req->config_set_absolute_path, &download_cmd, &cmd_buf_len) < 0) {
		syslog(LOG_ERR, "Failed to create list of packages to download");
		ret = -1;
	} else {
		system(download_cmd);
	}

	free(download_cmd);

	return ret;
}

int compress_packages(const upgrade_request_t *req) {
	UNUSED(req);
	return 0;
}
