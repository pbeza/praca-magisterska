project("${MAIN_PROJECT_NAME}-cli" VERSION 0.1 LANGUAGES C)

set(INC_DIR_CLIENT "${INC_DIR}/client")
include_directories(${INC_DIR_CLIENT})

configure_file("${INC_DIR_CLIENT}/config.h.in" "config.h")

# Create executable.

add_executable(${PROJECT_NAME} "main.c" "security.c" "config_parser.c" "config_parser_argv.c" "config_parser_file.c" "connection.c")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from common/*.in files.

target_include_directories(${PROJECT_NAME} PUBLIC ${PROJECT_BINARY_DIR})

# Include client's protocol implementation.

add_subdirectory(protocol)

# Link the executable to the common library.

target_link_libraries(${PROJECT_NAME} LINK_PUBLIC common client-protocol ${OPENSSL_LIBRARIES} ${LIBCONFIG_LIBRARIES})

# Generate manual from --help output.

set(HELP2MANUAL_CONFIG_PATH "../../client/manual.h2m")
set(MANUAL_FILENAME "${PROJECT_NAME}.1")
set_source_files_properties(${MANUAL_FILENAME} PROPERTIES GENERATED true)
#add_custom_command(TARGET doc POST_BUILD COMMAND)
add_custom_target(cli_doc help2man -i ${HELP2MANUAL_CONFIG_PATH} -o ${MANUAL_FILENAME} ./${PROJECT_NAME} VERBATIM)

# Installation rule.

install(TARGETS ${PROJECT_NAME} DESTINATION "mgr/${PROJECT_NAME}" COMPONENT "runtime")
