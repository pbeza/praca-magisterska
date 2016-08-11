#include <assert.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>

#include "common.h"
#include "debug.h"

#ifdef DEBUG

void vdebugnn(const char *fmt, va_list ap) {
	vfprintf(DEBUG_STREAM, fmt, ap);
}

void debugnn(const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vdebugnn(fmt, ap);
	va_end(ap);
}

void vdebug(const char *fmt, va_list ap) {
	char *newfmt = concat(fmt, "\n");
	vdebugnn(newfmt, ap);
	free(newfmt);
}

void debug(const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vdebug(fmt, ap);
	va_end(ap);
}

void vdebugnn_full(const char *fmt, va_list ap) {
	char *fmtprefix = __FILE__ ":" STR(__LINE__) ":" /*__func__ "():"*/;
	char *newfmt = concat(fmtprefix, fmt);
	vdebugnn(newfmt, ap);
	free(newfmt);
}

void debugnn_full(const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vdebugnn_full(fmt, ap);
	va_end(ap);
}

void vdebug_full(const char *fmt, va_list ap) {
	char *newfmt = concat(fmt, "\n");
	vdebugnn_full(newfmt, ap);
	free(newfmt);
}

void debug_full(const char *fmt, ...) {
	va_list ap;
	va_start(ap, fmt);
	vdebug_full(fmt, ap);
	va_end(ap);
}

#endif
