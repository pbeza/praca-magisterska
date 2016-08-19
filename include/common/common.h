/** \file
 * Commonly used functions and macros like \a MIN, \a MAX, \a ARRAY_LENGTH etc.
 */

#ifndef _COMMON_H
#define _COMMON_H

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <syslog.h>

#define STR_HELPER(x)			#x
#define STR(x)				STR_HELPER(x)

/**
 * Macro reporting fatal errors (via syslog), killing all processes in process'
 * group and exiting.
 * \note If this macro was implemented as function, than printing line number
 * of occured error using \a __LINE__ macro would be misleading.
 */
#define ERR(err_msg)			(closelog(),\
					syslog(LOG_EMERG, "%s:%d - %s - %m\n",\
						__FILE__, __LINE__, err_msg),\
					kill(0, SIGKILL),\
					exit(EXIT_FAILURE))

#define MIN(X, Y)			(((X) < (Y)) ? (X) : (Y))
#define MAX(X, Y)			(((X) > (Y)) ? (X) : (Y))

/**
 * Creates integer number with only i-th \p bit set to 1.
 */
#define BITMASK(bit)			(1 << bit)

/**
 * Set i-th bit in \p x to 1.
 */
#define SETBIT(x, bit)			(x |= (1 << bit))

/**
 * Returns non-zero number if i-th \p bit is set to 1.
 */
#define IS_SETBIT(x, bit)		((x >> bit) & 1)

/**
 * Macro for marking unused variables.
 * \note *Rationale* Pedantic compiler's option produce error/warning
 * (depending whether \c -Werror option is present) when unused variable is intruced.
 */
#define UNUSED(expr)			do { (void)(expr); } while (0)

/**
 * Returns length of given stack based array.
 */
#define ARRAY_LENGTH(x)			(sizeof(x) / sizeof((x)[0]))

/**
 * Concatenate two strings by reserving memory for concatenated word and copying
 * them into buffer. \warning User **must** free allocated memory by himself.
 */
char *concat(const char *s1, const char *s2);

ssize_t bulk_read(int fd, char *buf, size_t nbyte);

ssize_t bulk_write(int fd, char *buf, size_t nbyte);

#endif
