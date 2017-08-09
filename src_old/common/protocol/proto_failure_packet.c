#include <arpa/inet.h>
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <syslog.h>

#include "protocol/proto_failure_packet.h"

#include "network.h"
#include "protocol/packets.h"
#include "security.h"

#define ERR_CODE_LEN			2
#define ERR_CODE_OFFSET			HEADER_LEN
#define PROTO_FAILURE_LEN		HEADER_LEN + ERR_CODE_LEN

static int write_proto_failure_packet(char *buf, error_code err) {
	const uint16_t err_net = htons((uint16_t)err);

	if (write_header(buf, 0, PROTO_FAILURE) < 0) {
		syslog(LOG_ERR, "Failed to fill PROTO_FAILURE packet header");
		return -1;
	}

	*((uint16_t*)(buf + ERR_CODE_OFFSET)) = err_net;

	return 0;
}

int send_proto_failure(int socket, SSL *ssl, error_code err) {
	char buf[PROTO_FAILURE_LEN] = { 0 };
	int send_bytes;

	assert(err >= 0);

	if (write_proto_failure_packet(buf, err) < 0)
		return -1;

	send_bytes = ssl_send(socket, ssl, buf, PROTO_FAILURE_LEN);
	if (send_bytes != PROTO_FAILURE_LEN) {
		syslog(LOG_ERR, "Error while sending PROTO_FAILURE packet: "
		       "%d bytes sent (%d expected)", send_bytes, PROTO_FAILURE_LEN);
		return -1;
	}

	return 0;
}
