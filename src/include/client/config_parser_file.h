/** \file
 * Functions accessing configuration file of the client. Configuration read from
 * configuration file will overwrite static `INIT_CONFIG` but can be overwritten
 * by parameters passed via `argv[]`.
 */
#ifndef _CLIENT_CONFIG_PARSER_FILE_H
#define _CLIENT_CONFIG_PARSER_FILE_H

#include "common/config_parser_file.h"

#include "config.h"

int read_config_from_file(client_config_t *client_config);

#endif
