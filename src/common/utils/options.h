/**
 * @file
 * Universal `argv` options representation and basic parser used by both
 * server and client applications.
 */
#ifndef _OPTIONS_H
#define _OPTIONS_H

#include <stdint.h>

#include "common.h"

#ifdef POSIXLY_CORRECT
#define GETOPT getopt
#define OPTION(A, B, C, D, E, F) { A, B,    D, E, F }
#else
#define GETOPT getopt_long
#define OPTION(A, B, C, D, E, F) { A, B, C, D, E, F }
#endif

/**
 * Stores single runtime option read from `argv[]`.
 */
typedef struct option_t {
	/**
	 * Unique ID enumerated from 0.
	 * \note *Rationale:* this ID can be used as a index in array of options.
	 */
	const uint8_t id;
	/**
	  * Single character representing short option for `getopt()`.
	  */
	char short_option;
#ifndef POSIXLY_CORRECT
	/**
	 * String representing long option for `getopt_long()`.
	 * \note This variable is not defined if `POSIXLY_CORRECT` is defined.
	 */
	const char* long_option;
#endif
	/**
	 * Help description displayed when `--help` is present.
	 */
	const char* help_desc;
	/**
	 * Parameter's value name to be displayed with `--help` option.
	 * If parameter has no value use `NULL`.
	 */
	const char* help_value_name;
	/**
	 * Function handler called when this option is present in `argv[]`.
	 * If function pointer is `NULL` no function is called.
	 */
	void (*save)(const struct option_t* option, const char* value, void* config);
} option_t;

/**
 * Parse `argv` and save parsed results.
 */
void parse(int argc, char** argv, const char* optstring, const option_t* options, uint32_t* selected_options, void* config, const int n);

#endif
