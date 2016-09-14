project(common VERSION 0.1 LANGUAGES C)

include_directories("../../include/${PROJECT_NAME}")

configure_file("../../include/${PROJECT_NAME}/config.h.in" "config.h")

# Create executable.

add_library(common STATIC "daemonize.c" "argv_parser.c" "debug.c" "common.c" "network.c" "argv_parser.c" "security.c")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from common/*.in files.

target_include_directories(common PUBLIC ${PROJECT_BINARY_DIR})
