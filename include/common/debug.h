/** \file
 * Debug functions and macros printing errors on \a DEBUG_STREAM.
 *
 * \note Note that most of the time `syslog` is used for logging and debug.
 * Daemonized application is not able to print on `stdout` and `stderr`.
 */

#ifndef _DEBUG_H
#define _DEBUG_H

#include <errno.h>
#include <stdio.h>

#include "config.h" /* To import DEBUG symbol if defined */

#ifndef DEBUG

/*
 * If DEBUG symbol is not defined, than debug macros
 * and functions are translated into empty string.
 */

#define _debug(format, ap)
#define vdebugnn(...)
#define debugnn(...)
#define vdebug(...)
#define debug(...)
#define vdebugnn_full(...)
#define debugnn_full(...)
#define vdebug_full(...)
#define debug_full(...)

#else

/**
 * Which stream is used to print debug messages.
 */
#define DEBUG_STREAM			stderr

static inline void _debug(const char *format, va_list ap) {
	vfprintf(DEBUG_STREAM, format, ap);
}

/**
 * No new line after message is printed ('nn' = 'no newline').
 */
void vdebugnn(const char *fmt, va_list ap);
void debugnn(const char *fmt, ...);

/**
 * After specified message new line is appended.
 */
void vdebug(const char *fmt, va_list ap);
void debug(const char *fmt, ...);

/**
 * Before specified message prints filename, line number and function's name.
 * No new line after message is printed ('nn' = 'no newline').
 */
void vdebugnn_full(const char *fmt, va_list ap);
void debugnn_full(const char *fmt, ...);

/**
 * Before specified message prints filename, line number and function's name.
 * After specified message new line is printed.
 */
void vdebug_full(const char *fmt, va_list ap);
void debug_full(const char *fmt, ...);

#endif

#endif
