/** \file
 * Main loop of the server's daemon.
 */
#ifndef _CLIENT_MAIN_LOOP_H
#define _CLIENT_MAIN_LOOP_H

#include "argv_parser.h"

int connect_server(const client_config_t *config);

int send_hello_to_server(int fd);

#endif
