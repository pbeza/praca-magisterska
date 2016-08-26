/** \file
 * Main loop of the server's daemon.
 */
#ifndef _SERVER_MAIN_LOOP_H
#define _SERVER_MAIN_LOOP_H

#include "argv_parser.h"

void accept_clients(const server_config_t *config);

#endif
