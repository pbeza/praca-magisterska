/** \file
 * `UPGRADE_RESPONSE` packet related enumerations and functions definitions.
 */
#ifndef _PROTO_UPGRADE_RESPONSE_H
#define _PROTO_UPGRADE_RESPONSE_H

#include <openssl/ssl.h>

/**
 * Send `UPGRADE_RESPONSE` packet based on given parameters.
 * \param socket Socket used to send packet to client.
 * \param ssl    SSL object used to send packet to client.
 * \param len    Length of the send packet.
 * \param fd     File descriptor of the archive dedicated for the client.
 */
int send_upgrade_response(int socket, SSL *ssl, uint64_t len, int fd);

#endif
