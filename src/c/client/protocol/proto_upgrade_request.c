/** \file
 * `UPGRADE_REQUEST` packet related functions implementation.
 */
#include <arpa/inet.h>
#include <assert.h>
#include <stdint.h>
#include <syslog.h>

#include "protocol/proto_upgrade_request.h"

#include "common/protocol/packets.h"
#include "common/security.h"

static int write_upgrade_request(char *buf, uint16_t config_set,
				 compression_type compr_type,
				 package_mgr pkg_mgr,
				 uint32_t last_upgrade_time) {

	const uint16_t config_set_net = htons(config_set);
	const uint8_t  compr_type_net = (uint8_t)compr_type,
		       pkg_mgr_net = (uint8_t)pkg_mgr;
	const uint32_t last_upgrade_time_net = htonl(last_upgrade_time);

	if (write_header(buf, 0, UPGRADE_REQUEST) < 0) {
		syslog(LOG_ERR, "Failed to fill UPGRADE_REQUEST packet header");
		return -1;
	}

	*((uint16_t*)(buf + CONFIG_SET_OFFSET)) = config_set_net;
	*((uint8_t*)(buf + COMPR_TYPE_OFFSET)) = compr_type_net;
	*((uint8_t*)(buf + PKG_MGR_OFFSET)) = pkg_mgr_net;
	*((uint32_t*)(buf + LAST_UPGRADE_TIME_OFFSET)) = last_upgrade_time_net;

	return 0;
}

int send_upgrade_request(int socket, SSL *ssl, uint16_t config_set,
			 compression_type compr_type, package_mgr pkg_mgr,
			 uint32_t last_upgrade_time) {
	int send_bytes;
	char buf[UPGRADE_REQUEST_LEN] = { 0 };

	assert(compr_type >= 0);
	assert(pkg_mgr >= 0);

	if (write_upgrade_request(buf, config_set, compr_type, pkg_mgr,
				  last_upgrade_time) < 0) {
		syslog(LOG_ERR, "Failed to create UPGRADE_REQUEST packet");
		return -1;
	}

	send_bytes = ssl_send(socket, ssl, buf, UPGRADE_REQUEST_LEN);
	if (send_bytes != UPGRADE_REQUEST_LEN) {
		syslog(LOG_ERR, "Error while sending UPGRADE_REQUEST packet: "
		       "%d bytes sent (%d expected)", send_bytes, UPGRADE_REQUEST_LEN);
		return -1;
	}

	return 0;
}
