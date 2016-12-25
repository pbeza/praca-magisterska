/** \file
 * Commonly used miscellaneous simple functions and macros like \a MIN, \a MAX,
 * \a ARRAY_LENGTH etc.
 */
#ifndef _MISC_H
#define _MISC_H

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <syslog.h>

#define STR_HELPER(x)			#x
#define STR(x)				STR_HELPER(x)

/**
 * Maximum length of path.
 * \note There is `PATH_MAX` constant in `linux/limits.h` but it may be not
 * defined on all systems.
 */
#define PATH_MAX_LEN			4096

/**
 * Global variable to remember last signal number. This is useful for handling
 * SIGINT (Ctrl+C) signal.
 *
 * \note This is one of the few justified global variables in the project.
 */
extern volatile sig_atomic_t last_signal;

/**
 * Evaluate \p expression, and repeat as long as it returns -1 with `errno'
 * set to EINTR.
 * \note This macro is copied from `unistd.h` to make it more portable and to
 * not `define _GNU_SOURCE`.
 */
#define TEMP_FAILURE_RETRY(expression)	(__extension__\
					({ long int __result;\
					do __result = (long int) (expression);\
					while (__result == -1L && errno == EINTR);\
					__result; }))

/**
 * Macro reporting fatal (emergency) errors (via syslog).
 *
 * \note If this macro was implemented as function, than printing line number
 * of occured error using \a FILE and \a __LINE__ macros would be misleading.
 */
#define syslog_errno(err_msg)		(\
					syslog(LOG_CRIT, "CRITICAL ERROR "\
					       "%s:%d - %s - %m\n",\
						__FILE__, __LINE__, err_msg)\
					)

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

int set_sigint_handler();

/**
 * Concatenate two strings by reserving memory for concatenated word and copying
 * them into buffer. \warning User **must** free allocated memory by himself.
 */
char *concat(const char *s1, const char *s2);

ssize_t bulk_read(int fd, char *buf, size_t nbyte);

ssize_t bulk_pread(int fd, char *buf, size_t nbyte, off_t offset);

ssize_t bulk_write(int fd, char *buf, size_t nbyte);

int check_if_file_exists(const char *path);

int check_if_dir_exists(const char *path);

#endif
