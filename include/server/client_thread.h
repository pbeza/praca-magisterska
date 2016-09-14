/** \file
 * Thread dedicated for communication with single client.
 */
#ifndef _CLIENT_THREAD_H
#define _CLIENT_THREAD_H

#include "argv_parser.h"

/**
 * Structure passed to thread that talk to client. This structure contains both
 * common (eg. server's config) and per-thread settings (eg. socket's file
 * descriptor).
 * \warning Thread MUST `free` memory occupied by this structure.
 */
typedef struct thread_arg_t {
	/**
	 * Per-thread socket used to communicate with client.
	 */
	int csocket;
	/**
	 * Server configuration common for all threads.
	 */
	const server_config_t *server_config;
	/**
	 * Per-thread SSL structure for connection.
	 */
	SSL *ssl;
} thread_arg_t;

void* thread_work(thread_arg_t *arg);

#endif
