/** \file
 * `UPGRADE_REQUEST` packet related enumerations and functions declarations.
 */
#ifndef _PROTO_UPGRADE_REQUEST_H
#define _PROTO_UPGRADE_REQUEST_H

#include <openssl/ssl.h>

#include "common/protocol/packets.h"

/**
 * Send `UPGRADE_REQUEST` packet based on given parameters.
 */
int send_upgrade_request(int socket, SSL *ssl, uint16_t config_set,
			 compression_type compr_type, package_mgr pkg_mgr,
			 uint32_t last_upgrade_time);

#endif
