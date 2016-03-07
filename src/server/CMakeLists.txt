cmake_minimum_required(VERSION 3.1)
project(mgrsrv VERSION 0.1 LANGUAGES C)

add_executable(${PROJECT_NAME} "server.c" "common/utils/options.c")
