/** \file
 * Implementation of common for both client and server network-related functions.
 */
#include <sys/socket.h>
#include <unistd.h>

#include "network.h"

#include "misc.h"

ssize_t bulk_recv(int socket, char *buf, size_t length, int flags) {
	ssize_t c, len = 0;
	do {
		c = TEMP_FAILURE_RETRY(recv(socket, buf, length, flags));
		if (c < 0) return c;
		if (c == 0) break;
		buf += c;
		len += c;
		length -= c;
	} while (length > 0);
	return len;
}

ssize_t bulk_send(int socket, const char *buf, size_t length, int flags) {
	ssize_t c, len = 0;
	do {
		c = TEMP_FAILURE_RETRY(send(socket, buf, length, flags));
		if (c < 0) return c;
		buf += c;
		len += c;
		length -= c;
	} while (length > 0);
	return len;
}
