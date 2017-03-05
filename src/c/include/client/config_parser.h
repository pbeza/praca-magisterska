/** \file
 * Client's parser wrapper for `argv[]` and configuration file parsers.
 */
#ifndef _CLIENT_CONFIG_PARSER_H
#define _CLIENT_CONFIG_PARSER_H

#include "config.h"

/**
 * Initialize configuration in the following order (subsequent points overwrite
 * previous one):
 *  1. static default values,
 *  2. configuration file (overwrites 1),
 *  3. parsed `argv[]` options (overwrites 2).
 */

int load_config(int argc, char **argv, client_config_t *client_config);

#endif
