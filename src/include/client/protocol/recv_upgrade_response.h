/** \file
 * Functions for receiving `UPGRADE_RESPONSE` packet sent by server.
 */
#ifndef _RECV_UPGRADE_RESPONSE_H
#define _RECV_UPGRADE_RESPONSE_H

#include <openssl/ssl.h>

/**
 * Receive `UPGRADE_RESPONSE` packet sent by server.
 * \warning This packet can be large - ie. larger than 2^32 bytes (~4.5GB).
 */
int recv_upgrade_response(int socket, SSL *ssl, const char *fpath);

#endif
