/** \file
 * Functions definitions for receiving `UPGRADE_REQUEST` packet sent by client.
 */
#include <arpa/inet.h>
#include <inttypes.h>
#include <stdint.h>
#include <string.h>
#include <syslog.h>

#include <openssl/ssl.h>

#include "protocol/recv_upgrade_request.h"

#include "common/protocol/packets.h"
#include "common/security.h"

/**
 * Read configuration set number from the buffer.
 */
static uint16_t read_config_set(const char *buf) {
	return ntohl(*((uint16_t*)(buf + CONFIG_SET_OFFSET)));
}

/**
 * Read compression type from the buffer.
 */
static compression_type read_compr_type(const char *buf) {
	const uint8_t compr_type = *((uint8_t*)(buf + COMPR_TYPE_OFFSET));
	return (compression_type)compr_type;
}

/**
 * Read package manager from the buffer.
 */
static package_mgr read_pkg_mgr(const char *buf) {
	const uint8_t pkg_mgr = *((uint8_t*)(buf + PKG_MGR_OFFSET));
	return (package_mgr)pkg_mgr;
}

/**
 * Read time of the client's last successful upgrade.
 */
static uint32_t read_last_upgrade_time(const char *buf) {
	const uint32_t last_upgrade_time = *((uint32_t*)(buf + LAST_UPGRADE_TIME_OFFSET));
	return ntohl(last_upgrade_time);
}

/**
 * Initialize structure representing client's request with respect to data
 * saved in buffer \p buf received from client.
 */
static void init_upgrade_request_struct(upgrade_request_t *u, const char *buf) {
	u->config_set = read_config_set(buf);
	u->compr_type = read_compr_type(buf);
	u->pkg_mgr = read_pkg_mgr(buf);
	u->last_upgrade_time = read_last_upgrade_time(buf);
	memset(&u->config_set_absolute_path, 0, sizeof(u->config_set_absolute_path));
}

int recv_upgrade_request(int socket, SSL *ssl,
			 upgrade_request_t *upgrade_request) {

	char buf[UPGRADE_REQUEST_LEN] = { 0 };
	uint16_t packet_type;

	if (ssl_read(socket, ssl, buf, UPGRADE_REQUEST_LEN) < 0) {
		syslog(LOG_ERR, "Failed to ssl_read() UPGRADE_REQUEST packet");
		return -1;
	}

	if ((packet_type = read_header_type(buf)) != UPGRADE_REQUEST) {
		syslog(LOG_ERR, "Unexpected header type received - "
		       "UPGRADE_REQUEST was expected (%" PRIu16 " packet type "
		       "received)", packet_type);
		return -1;
	}

	init_upgrade_request_struct(upgrade_request, buf);

	return 0;
}
