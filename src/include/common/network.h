/** \file
 * Common for both client and server network-related functions.
 */
#ifndef _NETWORK_H
#define _NETWORK_H

#include <stdint.h>

ssize_t bulk_recv(int socket, char *buf, size_t length, int flags);

ssize_t bulk_send(int socket, const char *buf, size_t length, int flags);

#endif
