project(server-protocol LANGUAGES C)

add_library(server-protocol STATIC "proto_upgrade_response.c" "recv_upgrade_request.c")
