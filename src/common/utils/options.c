#include <assert.h>
#include <string.h>

#include "options.h"

void  add_option(options_t* all_options, user_option_t* user_option) {
	char to_append[3] = { 0 };
	uint8_t i = all_options->options_number++ - 1;
	assert(i + 1 < MAX_OPTIONS_NUMBER);
	all_options->allowed_options[i] = (option_t) {
		.bit_index = i,
		.user_option = *user_option
	};
	assert(strlen(all_options->optstring) + 2 < MAX_OPTSTRING_LENGTH);
	to_append[0] = user_option->short_option;
	if (user_option->help_value_name)
		to_append[1] = ':';
	strcat(all_options->optstring, to_append);
}
