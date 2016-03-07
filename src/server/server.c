/**
 * @file Server's starting point.
 */

#include <stdlib.h>

#include "help.h"

static void fill_options(options_t* options) {
	/*add_option(options, 'h', "--help", "Prints help.", NULL, NULL);*/
}

int main(int argc, char** argv) {
	/**
	 * Server's runtime options set as parameters of this application.
	 */
	options_t options = INIT_OPTIONS;
	fill_options(&options);
	/*save_parsed_args(argc, argv);
	server_work();*/
	return EXIT_SUCCESS;
}
