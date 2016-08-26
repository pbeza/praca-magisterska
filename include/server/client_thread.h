/** \file
 * Thread dedicated for communication with single client.
 */
#ifndef _CLIENT_THREAD_H
#define _CLIENT_THREAD_H

typedef struct thread_arg_t {
	int csocket;
} thread_arg_t;

void* thread_work(thread_arg_t *arg);

#endif
