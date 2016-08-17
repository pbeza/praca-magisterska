project(common VERSION 0.1 LANGUAGES C)

configure_file("common_config.h.in" "common_config.h")

# Create executable.

add_library(common STATIC "daemonize.c" "options.c" "debug.c" "common.c" "network.c")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from common/*.in files.

target_include_directories(common PUBLIC ${PROJECT_BINARY_DIR})
