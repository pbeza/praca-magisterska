/** \file
 * Common for both client and server daemonization process, implemented with
 * respect to the `daemon(7)` manual.
 */
#ifndef _DAEMONIZE_H
#define _DAEMONIZE_H

#include "config.h"

/**
 * Daemonization wrapper around `sysv_daemonize()`.
 */
int daemonize(const base_config_t *config, int (*daemon_work)(const base_config_t*));

#endif
