/** \file
 * Establishing connection with server within client's daemon.
 */
#ifndef _CLIENT_CONNECTION_H
#define _CLIENT_CONNECTION_H

#include <netinet/in.h>

#include <openssl/ssl.h>

#include "config.h"

int connect_server(client_config_t *config);

int disconnect_server(int socket);

int run_protocol(SSL *ssl, int socket);

#endif
