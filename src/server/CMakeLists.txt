cmake_minimum_required(VERSION 3.1)
project(server VERSION 0.1 LANGUAGES C)

set(HELP2MANUAL_CONFIG_PATH "../../server/manual.h2m")
set(MANUAL_FILENAME "${PROJECT_NAME}.1")

configure_file("config.h.in" "config.h")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from *.in files.

include_directories(${PROJECT_BINARY_DIR})

# Create executable.

add_executable(${PROJECT_NAME} "server.c" "parser.c" "common/utils/options.c" "common/utils/debug.c" "common/utils/common.c")

# Generate manual from --help option.

set_source_files_properties(${MANUAL_FILENAME} PROPERTIES GENERATED true)
#add_custom_command(TARGET doc POST_BUILD COMMAND )
add_custom_target(srv_doc help2man -i ${HELP2MANUAL_CONFIG_PATH} -o ${MANUAL_FILENAME} ./${PROJECT_NAME} VERBATIM)
