/**
 * @file
 * Server's main file / starting point.
 */

#include <stdlib.h>

#include "server_parser.h"

static void server_work(const config_t* config) {
	UNUSED(config);
}

int main(int argc, char** argv) {
	/** Server's runtime configuration */
	config_t config = INIT_CONFIG;
	/** Parse argv and save parsed options */
	parse_argv(argc, argv, &config);
	/** Do server's work */
	server_work(&config);
	return EXIT_SUCCESS;
}
