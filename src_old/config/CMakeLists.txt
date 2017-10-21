project("${MAIN_PROJECT_NAME}-config" VERSION 0.1 LANGUAGES C)

set(SERVER_CONFIG_DIR "server")
configure_file("${SERVER_CONFIG_DIR}/server.conf.in" "${SERVER_CONFIG_DIR}/server.conf")
