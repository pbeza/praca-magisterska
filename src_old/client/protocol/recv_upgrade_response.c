/** \file
 * Functions for receiving `UPGRADE_RESPONSE` packet sent by server. This kind
 * of packet carries much data (packages, configuration etc.), thus can be
 * large. Protocol is adapted to send also files larger than 2^32 bytes (~4.5GB).
 */
#include <assert.h>
#include <fcntl.h>
#include <inttypes.h>
#include <sys/stat.h>
#include <unistd.h>

#include "protocol/recv_upgrade_response.h"

#include "common/protocol/packets.h"
#include "common/misc.h"
#include "common/security.h"

#define WRITE_CHUNK_LEN			MIN(1 << 20, SSIZE_MAX) /* = 1 MiB */

static uint64_t read_upgrade_response_length(const char *buf) {
	return ntohll(*((uint64_t*)(buf + UPGRADE_RESPONSE_LENGTH_OFFSET)));
}

int recv_upgrade_response(int socket, SSL *ssl, const char *fpath) {
	int fd;
	uint64_t file_len;
	uint16_t packet_type;
	ssize_t read_bytes, write_bytes;
	char buf[WRITE_CHUNK_LEN] = { 0 };

	if (ssl_read(socket, ssl, buf, UPGRADE_RESPONSE_LEN) < UPGRADE_RESPONSE_LEN) {
		syslog(LOG_ERR, "Failed to ssl_read() UPGRADE_RESPONSE packet");
		return -1;
	}

	if ((packet_type = read_header_type(buf)) != UPGRADE_RESPONSE) {
		syslog(LOG_ERR, "Unexpected header type received - "
		       "UPGRADE_RESPONSE was expected (%d packet type received)",
		       packet_type);
		return -1;
	}

	file_len = read_upgrade_response_length(buf);

	syslog(LOG_DEBUG, "Waiting for %" PRIu64 " bytes to be sent by server",
	       file_len);
	syslog(LOG_DEBUG, "Creating archive file %s", fpath);

	if ((fd = TEMP_FAILURE_RETRY(open(fpath, O_CREAT | O_WRONLY | O_EXCL))) < 0) {
		syslog_errno("Failed to create file for UPGRADE_RESPONSE archive");
		return -1;
	}

	while (file_len > 0) {
		read_bytes = ssl_read(socket, ssl, buf, WRITE_CHUNK_LEN);
		if (!read_bytes) {
			syslog(LOG_CRIT, "Unexpected EOF while reading socket");
			return -1;
		} else if (read_bytes < 0) {
			syslog(LOG_ERR, "Failed to read upgrade response");
			return -1;
		}
		file_len -= read_bytes;
		if ((write_bytes = bulk_write(fd, buf, read_bytes)) < 0) {
			syslog_errno("Failed to append bytes to the end of file");
			return -1;
		}
		assert(write_bytes == read_bytes);
	}

	if (TEMP_FAILURE_RETRY(close(fd) < 0)) {
		syslog_errno("Failed to close archive received from server");
		return -1;
	}

	return 0;
}
