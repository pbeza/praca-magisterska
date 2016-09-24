project(common VERSION 0.1 LANGUAGES C)

set(INC_DIR_COMMON "${INC_DIR}/${PROJECT_NAME}")
include_directories(${INC_DIR_COMMON})

configure_file("${INC_DIR_COMMON}/config.h.in" "config.h")

# Create executable.

add_library(common STATIC "daemonize.c" "config_parser_argv.c" "debug.c" "misc.c" "network.c" "security.c" "config_parser_file.c" "config.c")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from common/*.in files.

target_include_directories(common PUBLIC ${PROJECT_BINARY_DIR})
