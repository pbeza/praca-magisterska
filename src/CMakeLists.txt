###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###
#                                                                         #
#                   This is main CMake of the project.                    #
#                                                                         #
###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###   ###

## TYPICAL USAGE
#  Simplest compilation (should suffice for most users):
#      cd src && mkdir build && cd build && cmake .. && make

## DEBUG / RELEASE
#  To generate Makefile for Debug or Release version run:
#      cmake -D CMAKE_BUILD_TYPE=X ..
#  where X is 'Debug' or 'Release'.

## COMPILATION DETAILS
#  To see compilation details (i.e. compiler's flags) run:
#      make VERBOSE=1

## MORE
#  See www.cmake.org to learn more about CMake.

cmake_minimum_required(VERSION 3.1)

# Set project's name, version and programming language.

project(mgr VERSION 0.1 LANGUAGES C)

# Define a few constant values.

set(AUTHOR						"Patryk Bęza (patryk.beza@gmail.com)")
set(DOXYGEN_LANGUAGE			"English" CACHE STRING "Doxygen documentation language")
set(MANUAL_FILENAME				"${PROJECT_NAME}.1")

# Define user-configurable variables.

option(POSIXLY_CORRECT			"Don't use non-POSIX compliant extensions" OFF)
option(DEBUG_CMAKE_MESSAGES		"Print all CMake variables" OFF)

# Print some information about detected system.

message(STATUS "Detected system: ${CMAKE_SYSTEM} ${CMAKE_HOST_SYSTEM_PROCESSOR}.")

# Substitude CMake variables with their values in header files.

#configure_file("README.md.in"	"README.md")

# Include headers from ${PROJECT_BINARY_DIR} to allow inclusion
# dynamically generated headers generated from *.hpp.in files.

#include_directories(${PROJECT_BINARY_DIR})

# Add subprojects.

add_subdirectory("server")
add_subdirectory("client")

# Generate Doxygen based documentation if Doxygen is installed.

find_package(Doxygen REQUIRED)
configure_file("doxygen_template.dox.in" "doxygen_template.dox")
add_custom_target(doc ${DOXYGEN_EXECUTABLE} "doxygen_template.dox" VERBATIM)

# Debug list of all the CMake variables.

if (DEBUG_CMAKE_MESSAGES)
	get_cmake_property(_variableNames VARIABLES)
	foreach (_variableName ${_variableNames})
		message(STATUS "${_variableName}=${${_variableName}}")
	endforeach()
endif()
