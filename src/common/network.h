#ifndef _NETWORK_H
#define _NETWORK_H

#include <netinet/in.h> /* sockaddr_in */
#include <stdint.h>

ssize_t bulk_recv(int socket, char *buffer, size_t length, int flags);

ssize_t bulk_send(int socket, const char *buffer, size_t length, int flags);

#endif
