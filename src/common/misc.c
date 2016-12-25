/** \file
 * Implementation of commonly used miscellaneous simple functions and macros
 * like \a MIN, \a MAX, \a ARRAY_LENGTH etc.
 */
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "misc.h"

volatile sig_atomic_t last_signal = 0;

static void sigint_handler(int sig) {
	last_signal = sig;
}

static int sethandler(void (*f)(int), int sig) {
	struct sigaction act = { 0 };
	act.sa_handler = f;
	return sigaction(sig, &act, NULL);
}

int set_sigint_handler() {
	return sethandler(sigint_handler, SIGINT);
}

char *concat(const char *s1, const char *s2) {
	const int n1 = strlen(s1);
	const int n2 = strlen(s2);
	char *s = malloc(n1 + n2 + 1);
	if (!s) {
		syslog_errno("malloc()");
	} else {
		strcpy(s, s1);
		strcat(s, s2);
	}
	return s; /** \warning User has to free() returned allocated space */
}

ssize_t bulk_read(int fd, char *buf, size_t nbyte) {
	ssize_t c;
	size_t len = 0;
	do {
		c = TEMP_FAILURE_RETRY(read(fd, buf, nbyte));
		if (c < 0) return c;
		if (c == 0) break;
		buf += c;
		len += c;
		nbyte -= c;
	} while (nbyte > 0);
	return len;
}

ssize_t bulk_pread(int fd, char *buf, size_t nbyte, off_t offset) {
	ssize_t c, len = 0;
	do {
		c = TEMP_FAILURE_RETRY(pread(fd, buf, nbyte, offset));
		if (c < 0) return c;
		if (c == 0) break;
		buf += c;
		len += c;
		nbyte -= c;
		offset += c;
	} while (nbyte > 0);
	return len;
}

ssize_t bulk_write(int fd, char *buf, size_t nbyte) {
	ssize_t c, len = 0;
	do {
		c = TEMP_FAILURE_RETRY(write(fd, buf, nbyte));
		if (c < 0) return c;
		buf += c;
		len += c;
		nbyte -= c;
	} while (nbyte > 0);
	return len;
}

static int check_if_exists(const char *path, int expect_file) {
	struct stat s;

	if (stat(path, &s) < 0) {
		if (errno != ENOENT && errno != EACCES && errno != ENOTDIR)
			syslog_errno("Failed to stat file");
		return -1;
	}

	if (expect_file) {
		if (!S_ISREG(s.st_mode))
			return -1;
	} else {
		if (!S_ISDIR(s.st_mode))
			return -1;
	}

	return 0;
}

int check_if_file_exists(const char *path) {
	return check_if_exists(path, 1);
}

int check_if_dir_exists(const char *path) {
	return check_if_exists(path, 0);
}
