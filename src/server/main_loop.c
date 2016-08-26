#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <arpa/inet.h>
#include <errno.h>
#include <pthread.h>
#include <signal.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>

#include "argv_parser.h"
#include "client_thread.h"
#include "common/common.h"
#include "common/network.h"

#define BACKLOG				MIN(64, SOMAXCONN)
#define MAX_CLIENTS_THREADS		2 /* \todo increase to 1 << 14 = 16384 */

/*
static pthread_t threads[MAX_CLIENTS_THREADS];
*/
static volatile int clients_number = 0;
static pthread_mutex_t clients_number_mutex = PTHREAD_MUTEX_INITIALIZER;

static void* thread_work_wrapper(void *arg) {
	thread_arg_t *thread_arg = (thread_arg_t*)arg;
	int csocket = thread_arg->csocket;
	void *ret = thread_work(thread_arg);

	free(arg);

	pthread_mutex_lock(&clients_number_mutex);
	clients_number--;
	pthread_mutex_unlock(&clients_number_mutex);

	syslog(LOG_INFO, "Closing client's socket and exiting from thread "
	       "talking with client; %d clients' thread(s) after this thread "
	       "terminatation", clients_number);

	syslog(LOG_DEBUG, "Closing client's socket no. %d", csocket);

	if (TEMP_FAILURE_RETRY(close(csocket)) < 0)
		syslog(LOG_CRIT, "Can't close() socket no. %d dedicated for "
		       "client; details: %m", csocket);
	return ret;
}

/**
 * Initialize thread's data passed to thread as an argument.
 * \warning Memory must freed by thread.
 */
static thread_arg_t* init_thread_arg(int csocket) {
	thread_arg_t *a = calloc(1, sizeof(thread_arg_t));
	if (!a)
		syslog(LOG_CRIT, "Can't reserve memory for thread's arg;"
		       "details: %m");
	else
		a->csocket = csocket;
	return a;
}

static int create_thread_for_client(int csocket) {
	int ret = 0;
	pthread_t t;
	pthread_attr_t attr;
	thread_arg_t *thread_arg;

	syslog(LOG_INFO, "Creating thread dedicated for connected client");

	if (pthread_attr_init(&attr)) {
		syslog(LOG_CRIT, "pthread_attr_init() failed; details: %m");
		return -1;
	}
	pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

	thread_arg = init_thread_arg(csocket);
	if (!thread_arg) {
		ret = -1;
	} else if (pthread_create(&t, &attr, thread_work_wrapper, thread_arg)) {
		syslog(LOG_CRIT, "Can't create thread for client using "
		       "pthread_create() function; details: %m");
		ret = -1;
	}

	if (pthread_attr_destroy(&attr)) {
		syslog(LOG_CRIT, "pthread_attr_destroy() failed; details: %m");
		ret = -1;
	}

	return ret;
}

static int try_to_create_thread_for_client(int csocket) {
	int ret = 0, too_many_threads = 0;

	pthread_mutex_lock(&clients_number_mutex);
	too_many_threads = clients_number >= MAX_CLIENTS_THREADS;
	if (!too_many_threads)
		clients_number++;
	pthread_mutex_unlock(&clients_number_mutex);

	if (too_many_threads) {
		syslog(LOG_WARNING, "Maximum clients' threads exist(ed)");
		ret = -1;
	} else {
		ret = create_thread_for_client(csocket);
	}

	return ret;
}

static int accept_client(int ssocket) {
	char *client_ip;
	socklen_t caddr_len = 0;
	struct sockaddr caddr = { 0 };
	struct sockaddr_in *caddr_in;
	int csocket = TEMP_FAILURE_RETRY(accept(ssocket, &caddr, &caddr_len));

	if (csocket < 0) {
		syslog(LOG_CRIT, "Failed to accept() client; details: %m");
		return -1;
	}

	caddr_in = (struct sockaddr_in*)&caddr;
	client_ip = inet_ntoa(caddr_in->sin_addr);

	syslog(LOG_INFO, "Connection accepted from client %s", client_ip);

	return csocket;
}

static void init_sockaddr(struct sockaddr_in* addr, uint16_t port) {
	memset(addr, 0, sizeof(struct sockaddr_in));
	addr->sin_family = AF_INET;
	addr->sin_port = htons(port);
	addr->sin_addr.s_addr = htonl(INADDR_ANY);
}

static int listen_on_port(uint16_t port) {
	struct sockaddr_in addr;
	int reuse = 1;
	int fd = socket(PF_INET, SOCK_STREAM, 0);
	if (fd < 0)
		ERR("socket");
	init_sockaddr(&addr, port);
	/* http://stackoverflow.com/questions/14388706/socket-options-so-reuseaddr-and-so-reuseport-how-do-they-differ-do-they-mean-t */
	/* \todo Check if other setsockopt options would be helpful. See: man 7 ip */
	if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)))
		ERR("setsockopt");
	if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0)
		ERR("bind - check whether other daemon instance is running");
	if (listen(fd, BACKLOG) < 0)
		ERR("listen");
	return fd;
}

void accept_clients(const server_config_t *config) {
	int port = config->base_config.port;
	int ssocket = listen_on_port(port);
	int csocket;

	while (1) { /* \todo daemon should be cancelable/abortable */
		syslog(LOG_INFO, "Server's main thread waiting for a new client...");

		csocket = accept_client(ssocket);

		if (csocket < 0) {
			syslog(LOG_CRIT, "Failed to accept client connection");
			continue;
		}

		syslog(LOG_INFO, "New client accepted successfully on socket "
		       "no. %d", csocket);

		if (try_to_create_thread_for_client(csocket) < 0) {
			syslog(LOG_CRIT, "Failed to create thread for client");

			if (TEMP_FAILURE_RETRY(close(csocket)) < 0)
				syslog(LOG_CRIT, "Can't close() socket "
				       "dedicated for client after thread "
				       "creation failure");
		}
	}

	if (TEMP_FAILURE_RETRY(close(ssocket)) < 0)
		ERR("close");
}
