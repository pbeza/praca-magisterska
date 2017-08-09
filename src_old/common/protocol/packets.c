/** \file
 * Implementation of common packets' access functions.
 */
#include <arpa/inet.h>
#include <assert.h>
#include <string.h>

#include <openssl/ssl.h>

#include "security.h"
#include "protocol/packets.h"

/**
 * Protocol version number.
 */
#define PROTO_VER			1

/**
 * @{ Access functions for packet's protocol version.
 */

uint8_t read_proto_ver(const char *buf) {
	return buf[0] >> 4;
}

static int write_proto_ver(char *buf) {
	const uint8_t mask = 0xf0;
	buf[0] = (buf[0] & ~mask) | ((PROTO_VER << 4) & mask);
	return 0;
}

/**
 * @}
 * @{ Access functions for packet's header flags.
 */

uint16_t read_header_flags(const char *buf) {
	const uint8_t hi = *((uint8_t*)buf) & 0x0f,
		      lo = *((uint8_t*)(buf + 1));
	return ((uint16_t)hi << 12) | lo;
}

static int write_header_flags(char *buf, uint16_t flags) {
	const uint8_t hi = (flags & 0x0f00) >> 8,
		      lo = flags & 0xff,
		      mask = 0x0f;
	buf[0] = (buf[0] & ~mask) | (hi & mask);
	buf[1] = lo;
	return 0;
}

/**
 * @}
 * @{ Access functions for packet's header type.
 */

uint16_t read_header_type(const char *buf) {
	return ntohs(*((uint16_t*)(buf + 2)));
}

static int write_header_type(char *buf, packet_type type) {
	assert(type >= 0);
	const uint16_t t = htons((uint16_t)type);
	memcpy(buf + 2, &t, sizeof(t));
	return 0;
}

/**
 * @}
 * @{ Access functions for whole packet's header.
 */

int write_header(char *buf, uint16_t flags, packet_type type) {
	memset(buf, 0, HEADER_LEN);
	write_proto_ver(buf);
	write_header_flags(buf, flags);
	write_header_type(buf, type);
	return 0;
}

int read_header(SSL *ssl, int socket, char *buf) {
	return ssl_read(socket, ssl, buf, HEADER_LEN);
}

/**
 * @}
 */
