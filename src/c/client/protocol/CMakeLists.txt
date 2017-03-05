project(client-protocol LANGUAGES C)

add_library(client-protocol STATIC "proto_upgrade_request.c" "recv_upgrade_response.c")
