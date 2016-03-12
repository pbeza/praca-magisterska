#include <stdio.h>
#include <string.h>

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
	/* User has to free returned allocated space */
	return s;
}
