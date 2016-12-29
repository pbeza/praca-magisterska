project("${MAIN_PROJECT_NAME}-srv" VERSION 0.1 LANGUAGES C)

set(INC_DIR_SERVER "${INC_DIR}/server")
include_directories(${INC_DIR_SERVER})

configure_file("${INC_DIR_SERVER}/config.h.in" "config.h")

# Create executable.

add_executable(${PROJECT_NAME} "main.c" "main_loop.c" "security.c" "config_parser.c" "config_parser_argv.c" "config_parser_file.c" "client_thread.c" "packages_manager.c")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from server/*.in files.

target_include_directories(${PROJECT_NAME} PUBLIC ${PROJECT_BINARY_DIR})

# Include server's protocol implementation.

add_subdirectory(protocol)

# Find and link against pthread library.

set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
find_package(Threads REQUIRED)

# Link the executable to the common libraries.

target_link_libraries(${PROJECT_NAME} LINK_PUBLIC common server-protocol ${CMAKE_THREAD_LIBS_INIT} ${OPENSSL_LIBRARIES} ${LIBCONFIG_LIBRARIES})

# Generate manual from --help output.

set(HELP2MANUAL_CONFIG_PATH "../../server/manual.h2m")
set(MANUAL_FILENAME "${PROJECT_NAME}.1")
set_source_files_properties(${MANUAL_FILENAME} PROPERTIES GENERATED true)
#add_custom_command(TARGET doc POST_BUILD COMMAND)
add_custom_target(srv_doc help2man -i ${HELP2MANUAL_CONFIG_PATH} -o ${MANUAL_FILENAME} ./${PROJECT_NAME} VERBATIM)

# Installation rule.

install(TARGETS ${PROJECT_NAME} DESTINATION "mgr/${PROJECT_NAME}" COMPONENT "runtime")
