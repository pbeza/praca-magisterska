/** \file
 * Common packets' types, definitions and access functions.
 */
#ifndef _COMMON_PACKETS_H
#define _COMMON_PACKETS_H

#include <endian.h>
#include <limits.h>
#include <stdint.h>

/**
 * Total header length in bytes.
 */
#define HEADER_LEN			4

/******************************************************************************
 * @{ UPGRADE_REQUEST and UPGRADE_RESPONSE common enums and definitions.
 *****************************************************************************/

/**
 * All of the supported packages and configuration compressions methods.
 */
typedef enum {
	NO_COMPRESSION,
	TAR_GZ_COMPRESSION,
	TAR_BZ2_COMPRESSION,
	TAR_XZ_COMPRESSION,
	RAR_COMPRESSION,
	ZIP_COMPRESSION
} compression_type;

/**
 * All of the supported packages managers.
 */
typedef enum {
	DPKG_PKG_MGR,
	TAR_XZ_PKG_MGR
} package_mgr;

/**
 * UPGRADE_REQUEST offsets.
 */
#define CONFIG_SET_LEN			2
#define CONFIG_SET_OFFSET		HEADER_LEN
#define COMPR_TYPE_LEN			1
#define COMPR_TYPE_OFFSET		CONFIG_SET_OFFSET + CONFIG_SET_LEN
#define PKG_MGR_LEN			1
#define PKG_MGR_OFFSET			COMPR_TYPE_OFFSET + COMPR_TYPE_LEN
#define LAST_UPGRADE_TIME_LEN		4
#define LAST_UPGRADE_TIME_OFFSET	PKG_MGR_OFFSET + PKG_MGR_LEN
#define UPGRADE_REQUEST_LEN		HEADER_LEN		+\
					CONFIG_SET_LEN		+\
					COMPR_TYPE_LEN		+\
					PKG_MGR_LEN		+\
					LAST_UPGRADE_TIME_LEN


/******************************************************************************
 * @}
 * @{ UPGRADE_REQUEST and UPGRADE_RESPONSE common enums and definitions.
 *****************************************************************************/

#define UPGRADE_RESPONSE_LENGTH_LEN	HEADER_LEN + 8
#define UPGRADE_RESPONSE_LENGTH_OFFSET	HEADER_LEN
#define UPGRADE_RESPONSE_LEN		HEADER_LEN		+\
					UPGRADE_RESPONSE_LENGTH_LEN

/******************************************************************************
 * @}
 * @{ Header related functions common for both client and server.
 *****************************************************************************/

/**
 * @{ 64-bit macros equivalent of `ntohl` and `htonl` macros.
 * \warning `uint64_t` and `endian.h` header are not guaranteed to exist but
 * it's very difficult and suboptimal to simulate one. Most of the OSes provide
 * both `uint64_t` and `endian.h`.
 */
#define ntohll(x)			( be64toh(x) )
#define htonll(x)			( htobe64(x) )

/**
 * @}
 * All of the packet types recognized by the protocol.
 */
typedef enum {
	UPGRADE_REQUEST,
	UPGRADE_RESPONSE,
	UPGRADE_STATUS,
	PROTO_FAILURE
} packet_type;

/**
 * Read protocol version from packet header.
 */
uint8_t read_proto_ver(const char *buf);

/**
 * Read protocol flags from packet header.
 */
uint16_t read_header_flags(const char *buf);

/**
 * Read packet type from packet header.
 */
uint16_t read_header_type(const char *buf);

/**
 * Write packet header into buffer \p buf.
 */
int write_header(char *buf, uint16_t flags, packet_type type);

/**
 * Read packet header from socket and save it in buffer.
 */
int read_header(SSL *ssl, int socket, char *buf);

/**
 * @}
 */

#endif
