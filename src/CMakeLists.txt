# This is main CMake of the project. Simplest compilation (should suffice for
# most users):
#
#   cd src && mkdir build && cd build && cmake .. && make && make install
#
# To generate Makefile for Debug or Release version run:
#
#   cmake -D CMAKE_BUILD_TYPE=X ..
#
# where X is 'Debug' or 'Release' (default). To see compilation details (i.e.
# compiler's flags) run 'make VERBOSE=1'. To see Makefile targets run 'make help'.
#
# Visit www.cmake.org to learn more about CMake.

cmake_minimum_required(VERSION 3.1)
project(appsync VERSION 0.1 LANGUAGES C)

###############################################################################
# Setting constants, options and printing basic information                   #
###############################################################################

# Few constant values.

set(AUTHOR "Patryk Bęza")
set(AUTHOR_EMAIL "patryk.beza@gmail.com")
set(DOXYGEN_LANGUAGE "English" CACHE STRING "Doxygen documentation language")
set(MAIN_PROJECT_NAME ${PROJECT_NAME})

# Add directory with CMake find modules scripts for not (yet) supported software.

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")

# User-configurable variables.

option(POSIXLY_CORRECT "Don't use non-POSIX compliant extensions" OFF)
option(DEBUG_CMAKE_MESSAGES "Print all CMake variables" OFF)
if (${CMAKE_BUILD_TYPE} MATCHES Debug)
	option(DEBUG "Constant propagated to source files indicating whether debug compilation is active" ON)
endif()

# Print basic information about detected system.

message(STATUS "Detected system: ${CMAKE_SYSTEM} ${CMAKE_HOST_SYSTEM_PROCESSOR}.")

# Substitude CMake variables with their values in header files.

configure_file("README.md.in" "README.md")

###############################################################################
# Common for both client and server third party libraries and applications    #
###############################################################################

# OPENSSL - Provides safe communication channel between client and server.

find_package(OpenSSL REQUIRED)
include_directories(${OPENSSL_INCLUDE_DIR})

# LIBCONFIG - Provides easy way to read/write from/to configuration file.

find_package(LibConfig REQUIRED)
include_directories(${LIBCONFIG_INCLUDE_DIR})

###############################################################################
# Handy (but not required) tools for developing this project                  #
###############################################################################

# CTAGS - Make ctags symbols active if ctags is installed.

find_program(CTAGS_PATH ctags)
if (EXISTS ${CTAGS_PATH})
	add_custom_command(OUTPUT tags COMMAND ctags -R ${CMAKE_CURRENT_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
	add_custom_target(ctags DEPENDS tags)
#	add_dependencies(${PROJECT_NAME} tags)
else()
	message(WARNING "ctags is not installed - consider installing it")
endif()

# CSCOPE - Make cscope symbols active if cscope is installed.

set(INC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
find_program(CSCOPE_PATH cscope)
if (EXISTS ${CSCOPE_PATH})
	set(CSCOPE_OUTPUT_FILES cscope.in.out cscope.out cscope.po.out)
	add_custom_command(OUTPUT ${CSCOPE_OUTPUT_FILES} COMMAND cscope -b -q -R -s ${CMAKE_CURRENT_SOURCE_DIR} -s ${INC_DIR})
	add_custom_target(cscope DEPENDS ${CSCOPE_OUTPUT_FILES})
else()
	message(WARNING "cscope is not installed - consider installing it")
endif()

# Make developer's symbols (cscope + ctags) active in debug mode.

if(${CMAKE_BUILD_TYPE} MATCHES Debug AND EXISTS ${CTAGS_PATH} AND EXISTS ${CSCOPE_PATH})
	message(STATUS "Generating developer's symbols (cscope and ctags) in debug mode is active")
	add_custom_target(dev_symbols ALL DEPENDS ctags cscope)
else()
	add_custom_target(dev_symbols DEPENDS ctags cscope)
endif()

###############################################################################
# Compiler's settings                                                         #
###############################################################################

# Set warning level for GCC to maximum possible.

if(CMAKE_COMPILER_IS_GNUCC OR CMAKE_COMPILER_IS_GNUC)
	# TODO -Wno-format added because of '%m' warning for syslog
	set(GCC_CODE_QUALITY_FLAGS "-Wall -pedantic -Wextra -Wno-long-long -Werror -Wno-format")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${GCC_CODE_QUALITY_FLAGS}")
endif()

###############################################################################
# Including all subprojects                                                   #
###############################################################################

# Headers common for both client and server. Add ${PROJECT_BINARY_DIR} to
# headers directories to allow inclusion files from common directory, using
# 'common/' path prefix.

include_directories(${PROJECT_BINARY_DIR})

# Add all subdirectories with subprojects - every subproject has its own CMake.

add_subdirectory(common)
add_subdirectory(server)
add_subdirectory(client)

###############################################################################
# Documentation                                                               #
###############################################################################

# DOXYGEN - Generate Doxygen-based documentation if Doxygen is installed.

find_package(Doxygen REQUIRED)
set(DOXYGEN_TEMPLATE_FILENAME "doxygen_template.dox")
configure_file("../doc/doxygen/${DOXYGEN_TEMPLATE_FILENAME}.in" ${DOXYGEN_TEMPLATE_FILENAME})
add_custom_target(doc ${DOXYGEN_EXECUTABLE} ${DOXYGEN_TEMPLATE_FILENAME} DEPENDS srv_doc cli_doc VERBATIM)

###############################################################################
# Printing all CMake variables for debug purposes if requested to do so       #
###############################################################################

# Print list of all the CMake variables if requested to do so.

if (DEBUG_CMAKE_MESSAGES)
	get_cmake_property(_variableNames VARIABLES)
	foreach (_variableName ${_variableNames})
		message(STATUS "${_variableName}=${${_variableName}}")
	endforeach()
endif()
