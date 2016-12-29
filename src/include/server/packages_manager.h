/** \file
 * Server's package manager wrapper for downloading and archiving distro packages.
 */
#ifndef _SERVER_PACKAGE_MANAGER
#define _SERVER_PACKAGE_MANAGER

#include "config.h"
#include "protocol/recv_upgrade_request.h"

int download_missing_packages(const server_config_t *srv_conf,
			      const upgrade_request_t *req);

int compress_packages(const upgrade_request_t *req);

#endif
