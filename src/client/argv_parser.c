/** \file
 * Implementation of client's `argv` parser.
 */
#include <arpa/inet.h>
#include <getopt.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "argv_parser.h"

#define DESC_OPTION_VERSION		"Print client's version number."

static int init_server_addr(client_config_t *config) {
	struct sockaddr_in *addr = &config->serv_addr;
	uint16_t port = config->base_config.port;
	memset(addr, 0, sizeof(struct sockaddr_in));
	addr->sin_family = AF_INET;
	addr->sin_port = htons(port);
	/** \note We don't use `inet_aton` because it doesn't support IPv6. */
	if (inet_pton(AF_INET, config->serv_ip_str, &addr->sin_addr.s_addr) <= 0) {
		printf("Unexpected format of IPv4.\n");
		return -1;
	}
	return 0;
}

static int client_parse(int argc, char **argv, client_config_t *config) {
	int d = argc - optind;
	char *last = argv[argc - 1];
	if (d == 1) {
		config->serv_ip_str = last;
	} else if (d == 0 && !(strlen(last) == 2 && !strncmp(last, "--", 2))) {
		printf("Missing server's IP. See --" LONG_OPTION_HELP ".\n");
		return -1;
	} else {
		printf("Unexpected options. See --" LONG_OPTION_HELP ".\n");
		return -1;
	}
	return init_server_addr(config);
}

int parse(int argc, char **argv, client_config_t *config) {
	const option_t allowed_options[] = {
		SET_OF_COMMON_OPTIONS,
	};
	const int n = ARRAY_LENGTH(allowed_options);
	return common_parse(argc, argv, allowed_options, (void*)config, n) < 0 ?
		-1 : client_parse(argc, argv, config);
}
