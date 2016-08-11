#include <netinet/in.h> /* sockaddr_in */
#include <string.h> /* memset */
#include <sys/socket.h> /* socket */

#include "common.h"

/*int sethandler(void (*f)(int), int sig) {
	struct sigaction act;
	memset(&act, 0, sizeof(struct sigaction));
	act.sa_handler = f;
	return sigaction(sig, &act, NULL);
}*/
