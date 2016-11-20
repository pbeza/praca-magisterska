project(common-protocol LANGUAGES C)

add_library(common-protocol STATIC "packets.c" "proto_failure_packet.c")
