/** \file
 * `UPGRADE_RESPONSE` packet related functions implementation.
 */
#include <arpa/inet.h>
#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <syslog.h>

#include "protocol/proto_upgrade_response.h"

#include "common/protocol/packets.h"
#include "common/misc.h"
#include "common/security.h"

#define READ_CHUNK_LEN			MIN(1 << 20, SSIZE_MAX) /* = 1 MiB */

static int write_upgrade_response_length(char *buf, uint64_t len) {
	*((uint64_t*)(buf + UPGRADE_RESPONSE_LENGTH_OFFSET)) = htonll(len);
	return 0;
}

int send_upgrade_response(int socket, SSL *ssl, uint64_t len, int fd) {
	char buf[READ_CHUNK_LEN] = { 0 };
	ssize_t read_bytes, send_bytes;
	off_t file_offset = 0;

	if (write_header(buf, 0, UPGRADE_RESPONSE) < 0) {
		syslog(LOG_ERR, "Failed to fill UPGRADE_RESPONSE packet header");
		return -1;
	}

	if (write_upgrade_response_length(buf, len) < 0) {
		syslog(LOG_ERR, "Failed to fill UPGRADE_RESPONSE packet length field");
		return -1;
	}

	if (ssl_send(socket, ssl, buf, UPGRADE_RESPONSE_LEN) < UPGRADE_RESPONSE_LEN) {
		syslog_errno("Fatal error sending UPGRADE_RESPONSE header");
		return -1;
	}

	syslog(LOG_DEBUG, "File associated with file descriptor %d (file size: %"
	      PRIu64 " bytes) will be send to client", fd, len);

	/* Sending file could be implemented using sendfile() function but we
	 * want SSL support and POSIX compliance.
	 */
	while (len > 0) {
		/* It can be implemented using simple bulk_read */
		read_bytes = bulk_pread(fd, buf, READ_CHUNK_LEN, file_offset);
		if (!read_bytes) {
			syslog(LOG_CRIT, "Unexpected EOF reading file to send");
			return -1;
		} else if (read_bytes < 0) {
			syslog_errno("Fatal error reading archive to send");
			return -1;
		}
		file_offset += read_bytes;

		send_bytes = ssl_send(socket, ssl, buf, read_bytes);
		if (send_bytes < 0) {
			syslog_errno("Fatal error sending archive for client");
			return -1;
		}
		len -= send_bytes;

		if (send_bytes != read_bytes) {
			syslog(LOG_CRIT, "Error sending archive: send_bytes = "
			       "%zd, read_bytes = %zd (they should be equal)",
			       send_bytes, read_bytes);
			return -1;
		}
	}

	return 0;
}
