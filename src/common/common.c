#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "common.h"

/*int sethandler(void (*f)(int), int sig) {
	struct sigaction act;
	memset(&act, 0, sizeof(struct sigaction));
	act.sa_handler = f;
	return sigaction(sig, &act, NULL);
}*/

char *concat(const char *s1, const char *s2) {
	const int n1 = strlen(s1);
	const int n2 = strlen(s2);
	char *s = malloc(n1 + n2 + 1);
	if (!s)
		ERR("malloc");
	strcpy(s, s1);
	strcat(s, s2);
	return s; /** \warning User has to free returned allocated space */
}

ssize_t bulk_read(int fd, char *buf, size_t nbyte) {
	int c;
	size_t len = 0;
	do {
		c = TEMP_FAILURE_RETRY(read(fd, buf, nbyte));
		if (c < 0) return c;
		if (c == 0) return len;
		buf += c;
		len += c;
		nbyte -= c;
	} while (nbyte > 0);
	return len;
}

ssize_t bulk_write(int fd, char *buf, size_t nbyte) {
	int c;
	size_t len = 0;
	do {
		c = TEMP_FAILURE_RETRY(write(fd, buf, nbyte));
		if (c < 0) return c;
		buf += c;
		len += c;
		nbyte -= c;
	} while(nbyte > 0);
	return len;
}
