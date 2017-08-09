#include "config.h"

/*
 * See:
 * http://stackoverflow.com/questions/16245521/c99-inline-function-in-c-file/16245669#16245669
 */
int is_option_set(const base_config_t *base_config, int opt);
int is_dont_daemonize_set(const base_config_t *base_config);
int is_print_help_set(const base_config_t *base_config);
int is_print_version_set(const base_config_t *base_config);
