project(server VERSION 0.1 LANGUAGES C)

include_directories("../../include/${PROJECT_NAME}")

configure_file("../../include/${PROJECT_NAME}/config.h.in" "config.h")

# Create executable.

add_executable(${PROJECT_NAME} "main.c" "argv_parser.c" "main_loop.c" "client_thread.c")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion dynamically
# generated headers generated from server/*.in files.

target_include_directories(${PROJECT_NAME} PUBLIC ${PROJECT_BINARY_DIR})

# Find and link against pthread library

set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
find_package(Threads REQUIRED)

# Link the executable to the common library.

target_link_libraries (${PROJECT_NAME} LINK_PUBLIC common ${CMAKE_THREAD_LIBS_INIT})

# Generate manual from --help output.

set(HELP2MANUAL_CONFIG_PATH "../../${PROJECT_NAME}/manual.h2m")
set(MANUAL_FILENAME "${PROJECT_NAME}.1")
set_source_files_properties(${MANUAL_FILENAME} PROPERTIES GENERATED true)
#add_custom_command(TARGET doc POST_BUILD COMMAND )
add_custom_target(srv_doc help2man -i ${HELP2MANUAL_CONFIG_PATH} -o ${MANUAL_FILENAME} ./${PROJECT_NAME} VERBATIM)

# Installation rule.

install(TARGETS ${PROJECT_NAME} DESTINATION "mgr/${PROJECT_NAME}" COMPONENT "runtime")
