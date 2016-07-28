# This is main CMake of the project. Simplest compilation (should suffice for
# most users):
#
#   cd src && mkdir build && cd build && cmake .. && make && make install
#
# To generate Makefile for Debug or Release version run:
#
#   cmake -D CMAKE_BUILD_TYPE=X ..
#
# where X is 'Debug' or 'Release'. To see compilation details (i.e. compiler's
# flags) run:
#
#   make VERBOSE=1
#
# Visit www.cmake.org to learn more about CMake.

cmake_minimum_required(VERSION 3.1)
project(mgr VERSION 0.1 LANGUAGES C)

# Define a few constant values.

set(AUTHOR "Patryk Bęza (patryk.beza@gmail.com)")
set(DOXYGEN_LANGUAGE "English" CACHE STRING "Doxygen documentation language")

# Define user-configurable variables.

option(POSIXLY_CORRECT "Don't use non-POSIX compliant extensions" OFF)
option(DEBUG_CMAKE_MESSAGES "Print all CMake variables" OFF)

# Print basic information about detected system.

message(STATUS "Detected system: ${CMAKE_SYSTEM} ${CMAKE_HOST_SYSTEM_PROCESSOR}.")

# Substitude CMake variables with their values in header files.

configure_file("README.md.in" "README.md")

# Generate ctags symbols if ctags is installed.

#find_program(CTAGS_PATH ctags)
#if (NOT CTAGS_PATH)
#	message(FATAL_ERROR "ctags not found")
#else()
#	add_dependencies(${PROJECT_NAME} tags)
#endif()

add_custom_command(OUTPUT tags COMMAND ctags -R ${CMAKE_CURRENT_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
add_custom_target(ctags DEPENDS tags)

# Generate cscope symbols if cscope is installed.

set(CSCOPE_OUTPUT_FILES cscope.in.out cscope.out cscope.po.out)
add_custom_command(OUTPUT ${CSCOPE_OUTPUT_FILES} COMMAND cscope -b -q -R)
add_custom_target(cscope DEPENDS ${CSCOPE_OUTPUT_FILES})

# Set warning level for GCC and MSVC (MS Visual Studio) to maximum possible.

if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_GNUC)
	set(GCC_CODE_QUALITY_FLAGS "-Wall -pedantic -Wextra -Wno-long-long -Werror")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${GCC_CODE_QUALITY_FLAGS}")
endif()

# Add subprojects.

add_subdirectory(server)
add_subdirectory(client)

# Generate Doxygen based documentation if Doxygen is installed.

find_package(Doxygen REQUIRED)
configure_file("doxygen_template.dox.in" "doxygen_template.dox")
add_custom_target(doc ${DOXYGEN_EXECUTABLE} "doxygen_template.dox" DEPENDS srv_doc VERBATIM)

# Debug list of all the CMake variables.

if (DEBUG_CMAKE_MESSAGES)
	get_cmake_property(_variableNames VARIABLES)
	foreach (_variableName ${_variableNames})
		message(STATUS "${_variableName}=${${_variableName}}")
	endforeach()
endif()
