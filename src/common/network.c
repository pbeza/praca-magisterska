/** \file
 * Implementation of common for both client and server network-related functions.
 */
#include <sys/socket.h>
#include <unistd.h>

#include "network.h"

#include "common.h"

ssize_t bulk_recv(int socket, char *buffer, size_t length, int flags) {
	int c;
	size_t len = 0;
	do {
		c = TEMP_FAILURE_RETRY(recv(socket, buffer, length, flags));
		if (c < 0) return c;
		if (c == 0) return len;
		buffer += c;
		len += c;
		length -= c;
	} while (length > 0);
	return len;
}

ssize_t bulk_send(int socket, const char *buffer, size_t length, int flags) {
	int c;
	size_t len = 0;
	do {
		c = TEMP_FAILURE_RETRY(send(socket, buffer, length, flags));
		if (c < 0) return c;
		buffer += c;
		len += c;
		length -= c;
	} while(length > 0);
	return len;
}
