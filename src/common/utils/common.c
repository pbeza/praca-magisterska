#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "common.h"

void *xmalloc(size_t size, const char *errmsg) {
	void *x = malloc(size);
	if (!x) {
		perror(errmsg);
		exit(EXIT_FAILURE);
	}
	return x;
}

char *concat(const char *s1, const char *s2) {
	const char *errmsg = "String concatenation has failed";
	const int n1 = strlen(s1);
	const int n2 = strlen(s2);
	char *s = xmalloc(n1 + n2 + 1, errmsg);
	strcpy(s, s1);
	strcat(s, s2);
	return s; /* User has to free returned allocated space */
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
