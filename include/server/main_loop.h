/** \file
 * Main loop of the server's daemon.
 */
#ifndef _MAIN_LOOP_H
#define _MAIN_LOOP_H

#include "argv_parser.h"

void listen_clients(const server_config_t *config);

#endif
