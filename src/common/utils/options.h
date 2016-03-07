#ifndef _OPTIONS_H
#define _OPTIONS_H

#include <assert.h>
#include <stdint.h>
#include <string.h>

#define MAX_OPTIONS_NUMBER		32
#define MAX_OPTSTRING_LENGTH		128

/**
 * Stores single runtime option read from `argv[]`.
 */
typedef struct user_option_t {
	/**
	  * Single character representing short option for `getopt()`.
	  */
	char short_option;
#ifndef POSIXLY_CORRECT
	/**
	 * String representing long option for `getopt_long()`.
	 */
	const char* long_option;
#endif
	/**
	 * Help description displayed when `--help` is present.
	 */
	const char* help_desc;
	/**
	 * Parameter's value name to be displayed when `--help` is present.
	 * If parameter has no value use `NULL`.
	 */
	const char* help_value_name;
	/**
	 * Function handler called when this option is present in `argv[]`.
	 * If function pointer is `NULL` no function is called.
	 */
	void (*parser_fun)(const struct user_option_t* option, int argv_index);
} user_option_t;

/**
 * \var user_option_t with some metadata.
 */
typedef struct option_t {
	/**
	 * Bit's index in \var options_t.selected_options representing this
	 * option. Can be understood as unique option's ID.
	 */
	uint8_t bit_index;
	/**
	 * User's option definition.
	 */
	user_option_t user_option;
} option_t;

/**
 * Stores all allowed runtime options.
 */
typedef struct options_t {
	/**
	 * All allowed options.
	 */
	option_t allowed_options[MAX_OPTIONS_NUMBER];
	/**
	 * Selected runtime options are represented by single bits set to 1.
	 */
	uint32_t selected_options;
	/**
	 * Number of allowed options stored in \var allowed_options array.
	 */
	uint8_t options_number;
	/**
	 * `optstring` for `getopt_long()` function.
	 */
	char optstring[MAX_OPTSTRING_LENGTH];
} options_t;

/**
 * Initialized (zeroed) `options_t` object.
 */
static const options_t INIT_OPTIONS = { .optstring = ":\0" };

/**
 * Add new allowed option to set of all of the allowed options.
 */
void add_option(options_t* all_options, user_option_t* user_option);

#endif
