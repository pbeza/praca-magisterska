#include <arpa/inet.h>
#include <errno.h>
#include <pthread.h>
#include <signal.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>

#include "main_loop.h"

#include "argv_parser.h"
#include "client_thread.h"
#include "common/common.h"
#include "common/network.h"

#define BACKLOG				MIN(64, SOMAXCONN)
#define MAX_CLIENTS_THREADS		2 /* \todo increase to 1 << 14 = 16384 */

static volatile int clients_number = 0;
static pthread_mutex_t clients_number_mutex = PTHREAD_MUTEX_INITIALIZER;

/**
 * Atomically add new client to clients counter if limit is not reached.
 * \note This must be atomic operation since many threads use clients counter.
 */
static int atomic_add_client_counter() {
	int too_many_threads;

	pthread_mutex_lock(&clients_number_mutex);
	too_many_threads = clients_number >= MAX_CLIENTS_THREADS;
	if (!too_many_threads)
		clients_number++;
	pthread_mutex_unlock(&clients_number_mutex);

	return too_many_threads ? -1 : 0;
}

/**
 * Atomically remove new client from clients counter.
 * \note This must be atomic operation since many threads use clients counter.
 */
static void atomic_remove_client_counter() {
	pthread_mutex_lock(&clients_number_mutex);
	clients_number--;
	pthread_mutex_unlock(&clients_number_mutex);
}

/**
 * This function is executed by thread dedicated for client. This function is
 * wrapper around actual thread's work because it handles clean up of resources
 * passed from server's main thread.
 */
static void* thread_work_wrapper(void *arg) {
	thread_arg_t *thread_arg = (thread_arg_t*)arg;
	void *ret = thread_work(thread_arg);

	atomic_remove_client_counter();

	syslog(LOG_INFO, "Closing client's socket and exiting from thread "
	       "talking with client; %d clients' thread(s) after this thread "
	       "terminatation", clients_number);

	syslog(LOG_INFO, "Closing client's socket no. %d", thread_arg->csocket);

	if (TEMP_FAILURE_RETRY(close(thread_arg->csocket)) < 0)
		syslog_errno("Can't close() socket dedicated for client");

	free(arg); /* Note that thread_arg is casted from arg */

	return ret;
}

/**
 * Initialize thread's data passed to thread as an argument.
 * \warning Memory must `free()`d by thread!
 */
static thread_arg_t* init_thread_arg(const server_config_t *config, int csocket) {
	thread_arg_t *a = calloc(1, sizeof(thread_arg_t));
	if (a) {
		a->csocket = csocket;
		a->server_config = config;
	} else {
		syslog_errno("Can't reserve memory for thread's parameters");
	}
	return a;
}

/**
 * Create and start thread dedicated for client accepted by server.
 * \p thread_arg is parameter allocated by server's main thread for new thread.
 */
static int start_thread_for_client(thread_arg_t *thread_arg) {
	int ret = 0;
	pthread_t t;
	pthread_attr_t attr;

	/* This is diagnostic info, thus locking counter mutex is overkill */
	syslog(LOG_INFO, "Creating thread dedicated for connected client (%d"
	       " client(s) in total)", clients_number);

	if (pthread_attr_init(&attr)) {
		syslog_errno("pthread_attr_init() failed");
		return -1;
	}
	pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

	if (pthread_create(&t, &attr, thread_work_wrapper, thread_arg)) {
		syslog_errno("Can't create thread for client using "
			    "pthread_create() function");
		ret = -1;
	}

	if (pthread_attr_destroy(&attr)) {
		syslog_errno("pthread_attr_destroy() failed");
		return -1;
	}

	return ret;
}

/**
 * Wrapper function for adding client to atomic counter and starting new thread.
 */
static int try_to_create_thread_for_client(thread_arg_t *thread_arg) {
	int ret;

	if ((ret = atomic_add_client_counter()) < 0)
		syslog(LOG_WARNING, "Maximum clients' threads exist(ed)");
	else if ((ret = start_thread_for_client(thread_arg)) < 0)
		atomic_remove_client_counter();

	return ret;
}

/**
 * Wrapper function for `accept()`, handling logging and potential failures.
 */
static int accept_client(int ssocket) {
	char *client_ip;
	socklen_t caddr_len = 0;
	struct sockaddr caddr = { 0 };
	struct sockaddr_in *caddr_in;
	int csocket = TEMP_FAILURE_RETRY(accept(ssocket, &caddr, &caddr_len));

	if (csocket < 0) {
		syslog_errno("Failed to accept() client");
		return -1;
	}

	caddr_in = (struct sockaddr_in*)&caddr;
	client_ip = inet_ntoa(caddr_in->sin_addr);

	syslog(LOG_INFO, "Connection accepted from client %s", client_ip);

	return csocket;
}

/**
 * Initialize `sockaddr_in` structure with given \p port.
 */
static void init_sockaddr(struct sockaddr_in* addr, uint16_t port) {
	memset(addr, 0, sizeof(struct sockaddr_in));
	addr->sin_family = AF_INET;
	addr->sin_port = htons(port);
	addr->sin_addr.s_addr = htonl(INADDR_ANY);
}

/**
 * Initialize server's \p socket, ie. set socket options, bind and listen on
 * given \p port number.
 */
static int init_server_socket(int socket, uint16_t port) {
	struct sockaddr_in addr;
	int reuse = 1;

	init_sockaddr(&addr, port);
	/* http://stackoverflow.com/questions/14388706/socket-options-so-reuseaddr-and-so-reuseport-how-do-they-differ-do-they-mean-t */
	/* \todo Check if other setsockopt options would be helpful. See: man 7 ip */
	if (setsockopt(socket, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse))) {
		syslog_errno("setsockopt() on server's socket has failed");
		return -1;
	}
	if (bind(socket, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
		syslog_errno("bind() has failed; check whether other daemon "
			    "instance is running");
		return -1;
	}
	if (listen(socket, BACKLOG) < 0) {
		syslog_errno("listen() has failed on server's socket");
		return -1;
	}
	return 0;
}

/**
 * Create and initialize server's listening socket.
 */
static int create_initialized_server_socket(uint16_t port) {
	int fd = socket(PF_INET, SOCK_STREAM, 0);
	if (fd < 0) {
		syslog_errno("Failed to create server's socket");
		return -1;
	}
	if (init_server_socket(fd, port) < 0) {
		if (TEMP_FAILURE_RETRY(close(fd)) < 0)
			syslog_errno("Can't close server's socket");
		return -1;
	}
	return fd;
}

/**
 * Main loop of server infinitely accepting connections from clients.
 */
int accept_clients(const server_config_t *config) {
	int port = config->base_config.port,
	    ssocket,
	    csocket,
	    ret = 0;
	thread_arg_t *thread_arg;

	if ((ssocket = create_initialized_server_socket(port)) < 0) {
		syslog(LOG_ERR, "Listening on port has failed");
		return -1;
	}

	while (1) { /** \todo daemon should be cancelable/abortable */
		syslog(LOG_INFO, "Server's main thread waiting for a new client...");

		if ((csocket = accept_client(ssocket)) < 0) {
			syslog(LOG_ERR, "Failed to accept client connection");
			continue;
		}

		syslog(LOG_INFO, "New client accepted successfully on socket "
		       "no. %d", csocket);

		/* `thread_arg` MUST be free() */
		if (!(thread_arg = init_thread_arg(config, csocket))) {
			syslog(LOG_ERR, "Failed to create thread's data thus "
			       "connection with client will be closed");
			ret = -1;
		} else if (try_to_create_thread_for_client(thread_arg) < 0) {
			syslog(LOG_ERR, "Failed to create thread for client");
			free(thread_arg);
			ret = -1;
		}

		if (ret < 0) {
			if (TEMP_FAILURE_RETRY(close(csocket)) < 0)
				syslog_errno("Can't close() socket dedicated for client");
			ret = 0;
		}
	}

	if (TEMP_FAILURE_RETRY(close(ssocket)) < 0) {
		syslog_errno("Closing server socket has failed");
		return -1;
	}

	return 0;
}
