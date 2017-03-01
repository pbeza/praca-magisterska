#include <ctype.h>
#include <regex.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "packages_manager.h"

#include "common/misc.h"
#include "package_archiver.h"

#define CHANGE_CWD_TO_PKG_CACHE_DIR_CMD	"cd '%s'"
#define APT_PKG_DOWNLOAD_CMD		"apt-get download" /* TODO apt-get install --download-only (into the package cache) */
#define APT_PKG_EXIST_CMD		"apt-cache show"
#define PKG_DOWNLOAD_CMD_RESIZE_FACTOR	2
#define MIN_PKG_DOWNLOAD_CMD_CHAR_LEN	4096
#define MAX_PKG_NAME_LEN		4096
#define CONFIG_SET_COMMENT_CHAR		'#'
#define VALID_PKG_REGEX			"^[[:alnum:][:alpha:]\\-\\_\\.\\+]+$"

static int check_if_ignore_pkg(const char *pkg_name, const regex_t *pkg_regex) {
	const size_t n = sizeof(APT_PKG_EXIST_CMD) + MAX_PKG_NAME_LEN;
	char pkg_exist_cmd[n];
	int ret;

	if (pkg_name[0] == '\0' || pkg_name[0] == CONFIG_SET_COMMENT_CHAR ||
	    regexec(pkg_regex, pkg_name, (size_t)0, NULL, 0) == REG_NOMATCH)
		return 1;

	snprintf(pkg_exist_cmd, n, "%s %s", APT_PKG_EXIST_CMD, pkg_name);

	ret = system(pkg_exist_cmd);
	if (ret) {
		syslog(LOG_DEBUG, "system(\"%s\") returned %d", pkg_exist_cmd, ret);
		syslog(LOG_ERR, "Package '%s' probably doesn't exist", pkg_name);
		return 1;
	} else {
		syslog(LOG_DEBUG, "Package '%s' probably exist", pkg_name);
	}

	return 0;
}

static char *trimwhitespace(char *str)
{
	char *end;

	while (isspace(*str))
		str++;

	if (*str == 0)
		return str;

	end = str + strlen(str) - 1;
	while (end > str && isspace(*end))
		end--;

	*(end + 1) = 0;

	return str;
}

static int append_pkg_list(const char *config_set_absolute_path,
			   char **download_cmd,
			   size_t *cmd_buf_len) {
	int ret = 0;
	FILE *file;
	size_t cmd_len = strlen(*download_cmd), line_no, pkg_count;
	char *fgets_res = NULL, *pkg_name_beg;
	char pkg_name[MAX_PKG_NAME_LEN];
	regex_t pkg_regex;

	ret = regcomp(&pkg_regex, VALID_PKG_REGEX, REG_EXTENDED | REG_ICASE);
	if (ret) {
		regerror(ret, &pkg_regex, pkg_name, MAX_PKG_NAME_LEN);
		syslog(LOG_ERR, "Failed to compile regex '%s' for checking if "
				"package names are valid; details: %s",
				VALID_PKG_REGEX, pkg_name);
		return -1;
	}

	do {
		file = fopen(config_set_absolute_path, "r");
	} while (!file && errno == EINTR);

	if (!file) {
		syslog(LOG_ERR, "Failed to open config set file %s", config_set_absolute_path);
		regfree(&pkg_regex);
		return -1;
	}

	for (pkg_count = 0, line_no = 1 ;; line_no++) {
		do {
			errno = 0;
		} while (!(fgets_res = fgets(pkg_name, sizeof(pkg_name), file)) && errno == EINTR);

		if (errno) {
			syslog_errno("fgets() failed reading config set");
			ret = -1;
			break;
		} else if (!fgets_res) {
			syslog(LOG_DEBUG, "%zu packages successfully read from config set '%s'",
			       pkg_count, config_set_absolute_path);
			break;
		}

		pkg_name_beg = trimwhitespace(pkg_name);
		if (check_if_ignore_pkg(pkg_name_beg, &pkg_regex)) {
			syslog(LOG_INFO, "Ignoring line %zu '%s' from file '%s'",
				line_no, pkg_name_beg, config_set_absolute_path);
			continue;
		}

		/* If we ran out of free space for command - realloc().
		 * +2 is for 1 space character and 1 trailing null byte.
		 */

		const size_t n = strcspn(pkg_name_beg, "\n"),
			     k = cmd_len + n + 2;

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
		strncpy(*download_cmd + cmd_len + 1, pkg_name_beg, n);
		cmd_len += n + 1; /* +1 for space character */
		(*download_cmd)[cmd_len] = '\0';
		pkg_count++;
	}

	if (TEMP_FAILURE_RETRY(fclose(file)) < 0) {
		syslog_errno("Failed to close() config set file");
		return -1;
	}

	regfree(&pkg_regex);

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
		ret = system(download_cmd);
		syslog(LOG_DEBUG, "system(\"%s\") returned %d", download_cmd, ret);
		if (ret)
			ret = -1;
	}

	free(download_cmd);

	if (ret < 0)
		syslog(LOG_ERR, "Failed to download packages");

	return ret;
}

int compress_packages(const upgrade_request_t *req) {
	UNUSED(req);
	const char test[2][1024] = { "/tmp/a.txt", "/tmp/b.txt" };
	const char *archive_path = "/tmp/test_archive";

	if (compress(archive_path, TAR_GZ_COMPRESSION, test, 2) < 0) {
		syslog(LOG_ERR, "Packages compression has failed");
		return -1;
	}

	return 0;
}
