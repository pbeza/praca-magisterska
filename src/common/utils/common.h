#ifndef _COMMON_H
#define _COMMON_H

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

#define STR_HELPER(x)			#x
#define STR(x)				STR_HELPER(x)
#define ERR(source) (fprintf(stderr,"%s:%d\n", __FILE__, __LINE__),\
		     perror(source),\
		     kill(0,SIGKILL),\
		     exit(EXIT_FAILURE))

#define MIN(X, Y) (((X) < (Y)) ? (X) : (Y))
#define MAX(X, Y) (((X) > (Y)) ? (X) : (Y))

/**
 * Macro for reporting errors and critical exit in multithreaded environment.
 */
/* TODO strerror_r */

/**
 * Set i-th bit to 1.
 */
#define SETBIT(x, bit)			(x |= (1 << bit))

/**
 * Check whether i-th bit is set to 1.
 */
#define IS_SETBIT(x, bit)		((x >> bit) & 1)

/**
 * Macro for marking unused variables.
 *
 * \note **RATIONALE** Pedantic compiler's option produce error/warning
 * (depending whether \c -Werror option is present) when unused variable is intruced.
 */
#define UNUSED(expr)			do { (void)(expr); } while (0)

/**
 * Returns length of given stack based array.
 */
#define ARRAY_LENGTH(x)			(sizeof(x) / sizeof((x)[0]))

/**
 * Allocate \p size bytes of memory. Display error given message if there is no
 * space left.
 */
void *xmalloc(size_t size, const char *errmsg);

/**
 * Concatenate two strings by reserving space for concatenated word and copying
 * them. \warning User **must** free allocated memory by himself.
 */
char *concat(const char *s1, const char *s2);

ssize_t bulk_read(int fd, char *buf, size_t nbyte);

#endif
