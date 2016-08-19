/** \file
 * Client's main file.
 */
#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <stdlib.h>

#include "argv_parser.h"

static void client_work(const client_config_t *config) {
	UNUSED(config);
}

int main(int argc, char** argv) {
	client_config_t config = INIT_CONFIG;
	int exit = parse_argv(argc, argv, &config);
	if (!exit) {
		openlog(PROJECT_NAME, LOG_PID | LOG_CONS | LOG_ODELAY, LOG_USER);
		client_work(&config);
		closelog();
	}
	return EXIT_SUCCESS;
}
