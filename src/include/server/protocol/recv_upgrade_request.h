/** \file
 * Functions declarations for receiving `UPGRADE_REQUEST` packet sent by client.
 */
#ifndef _RECV_UPGRADE_REQUEST_H
#define _RECV_UPGRADE_REQUEST_H

#include <openssl/ssl.h>

#include "common/protocol/packets.h"

/**
 * Detailes fetched from `UPGRADE_REQUEST` sent by client.
 */
typedef struct upgrade_request_t {
	uint16_t config_set;
	compression_type compr_type;
	package_mgr pkg_mgr;
	uint32_t last_upgrade_time;
} upgrade_request_t;

/**
 * Reveive `UPGRADE_REQUEST` packet sent by client and save details in
 * \p upgrade_request structure.
 */
int recv_upgrade_request(int socket, SSL *ssl,
			 upgrade_request_t *upgrade_request);

#endif
