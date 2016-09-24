/** \file
 * Establishing connection with server within client's daemon.
 */
#ifndef _CLIENT_CONNECTION_H
#define _CLIENT_CONNECTION_H

#include <netinet/in.h>

#include <openssl/ssl.h>

int connect_server(const struct sockaddr_in *addr);

int disconnect_server(int socket);

int send_hello_to_server(SSL *ssl, int socket);

#endif
