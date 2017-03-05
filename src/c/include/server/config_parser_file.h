/** \file
 * Functions accessing configuration file of the server. Configuration read from
 * configuration file will overwrite static `INIT_CONFIG` but can be overwritten
 * by parameters passed via `argv[]`.
 */
#ifndef _SERVER_CONFIG_PARSER_FILE_H
#define _SERVER_CONFIG_PARSER_FILE_H

#include "common/config_parser_file.h"

#include "config.h"

int read_config_from_file(server_config_t *server_config);

#endif
