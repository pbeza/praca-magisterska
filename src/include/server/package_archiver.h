/** \file
 * \c UPGRADE_RESPONSE data field compression.
 */
#ifndef _SERVER_PACKAGE_ARCHIVER_H
#define _SERVER_PACKAGE_ARCHIVER_H

#include "common/protocol/packets.h"

int compress(const char *archive_path, compression_type compr_type, const char paths[][1024], size_t count);

int extract(const char *archive_path);

#endif
