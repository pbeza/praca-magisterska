/** \file
 * `PROTO_FAILURE` packet implementation.
 */
#ifndef _PROTO_FAILURE_PACKET_H
#define _PROTO_FAILURE_PACKET_H

#include <openssl/ssl.h>

#include "packets.h"

typedef enum {
	UNKNOWN_PROTO_VER,
	UNKNOWN_FLAG,
	UNKNOWN_PKG_MGR,
	UNKNOWN_COMPR_TYPE,
	UNKNOWN_CONFIG_SET,
	UNKNOWN_PACKET_TYPE,
	MALFORMED_PACKET,
	SERVER_INTERNAL_ERR,
	CLIENT_INTERNAL_ERR
} error_code;

int send_proto_failure(int socket, SSL *ssl, error_code err);

#endif
