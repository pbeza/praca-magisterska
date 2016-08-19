/** \file
 * Functions for daemonizing application with respect to SysV init guide:
 * https://www.freedesktop.org/software/systemd/man/daemon.html#SysV%20Daemons
 */

#define _GNU_SOURCE /* TEMP_FAILURE_RETRY */

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "daemonize.h"
#include "common.h"

#define UNIQ_DAEMON_FILE_PERMISSION	0644

/**
  * Maximum number of digits in PID. This is needed for writing/reading PID
  * to/from `pid_fpath` file.
  */
#define MAX_DIGITS_IN_PID	9

/*static pid_t read_pid_from_file(int fd) {
	long pid;
	char buf[128] = { 0 }, *endptr;
	ssize_t len = bulk_read(fd, buf, sizeof(buf));
	if (len < 0)
		return len;
	errno = 0;
	pid = strtol(buf, &endptr, 10);
	return pid < 0 || buf == *endptr || errno != 0 ? -1 : pid;
}*/

static int assure_single_daemon_instance(const char *pid_fpath, int *fd) {
	char pid_str[MAX_DIGITS_IN_PID + 1] = { 0 };
	*fd = TEMP_FAILURE_RETRY(open(pid_fpath, O_CREAT | O_RDWR,
					 UNIQ_DAEMON_FILE_PERMISSION));
	if (*fd < 0)
		ERR("open");
	/* File locking to allow one daemon instance. Process' exit unlocks it. */
	if (TEMP_FAILURE_RETRY(lockf(*fd, F_TLOCK, 0)) < 0) {
		if (errno == EAGAIN || errno == EACCES)
			return -1;
		else
			ERR("lockf");
	}
	snprintf(pid_str, sizeof(pid_str), "%ld", (long)getpid());
	if (bulk_write(*fd, pid_str, strlen(pid_str)) < 0)
		ERR("can't write PID to file");
	/* DO NOT close *fd because it will release the file's lock! */
	return 0;
}

static void redirect_to_dev_null() {
	/* 9. Connect stdin, stdout, stderr to /dev/null */
	int fd;
	for (fd = 0; fd < 3; fd++)
		if (TEMP_FAILURE_RETRY(close(fd)) < 0)
			ERR("close");
	fd = TEMP_FAILURE_RETRY(open("/dev/null", O_RDWR));
	if (fd < 0)
		ERR("open for stdin");
	if (dup(fd) < 0)
		ERR("dup for stdout");
	if (dup(fd) < 0)
		ERR("dup for stderr");
}

static void daemon_work(int pipe_fd, const char *pid_fpath, int *pid_fd) {
	int ret = 0;
	redirect_to_dev_null();
	/* 10. Reset umask to 0. */
	umask(0);
	/* 11. Change the CWD to '/' to avoid that daemon blocks unmounts. */
	if (chdir("/") < 0)
		ERR("chdir");
	/* 12. Make sure that other instance of daemon is not working. */
	if (assure_single_daemon_instance(pid_fpath, pid_fd) < 0)
		ret = -1;
	/* 13. Dropping privileges is not applicable.
	 * 14. Notify original process that daemon was successfully created. */
	if (bulk_write(pipe_fd, (char*)&ret, sizeof(ret)) < 0)
		ERR("write to pipe in daemon");
	if (TEMP_FAILURE_RETRY(close(pipe_fd)) < 0)
		ERR("closing pipe in daemon");
	if (ret < 0) {
		syslog(LOG_WARNING, "Another instance of daemon is running");
		closelog();
		exit(EXIT_SUCCESS);
	}
}

static void first_child_work(int pipe_fd, const char *pid_fpath, int *pid_fd) {
	pid_t pid;
	/* 6. Detach from any terminal and create an independent session. */
	if (setsid() < 0)
		ERR("setsid");
	/* 7. Second fork() to ensure that the daemon can never re-acquire a
	 * terminal again. */
	if ((pid = fork()) < 0) {
		ERR("fork");
	} else if (pid) {
		if (TEMP_FAILURE_RETRY(close(pipe_fd)) < 0)
			ERR("closing pipe in daemon");
		closelog();
		/* 8. Exit in the first child. Ensures reparenting 2nd child. */
		exit(EXIT_SUCCESS);
	} else {
		daemon_work(pipe_fd, pid_fpath, pid_fd);
	}
}

/**
 * To understand why this daemonizing implementation consists of 15 steps, see:
 * https://www.freedesktop.org/software/systemd/man/daemon.html#SysV%20Daemons
 * \a pid_fd is file descriptor of locked file with daemon's PID. It can't be
 * closed as long as we want only one daemon's instance.
 *
 * \return 0 if application was daemonized, ie. it consists of one process
 * running in background. -1 if daemonization wasn't successfull because another
 * daemon instance exists or error occured.
 */
int sysv_daemonize(const char *pid_fpath, int *pid_fd) {
	/* Demonization consists of 15 steps. As long as demonization is the
	 * first thing we do in program, we can safely assume that:
	 * 1. All file descriptors > 3 are closed.
	 * 2. All signal handlers are set to their default.
	 * 3. Signal mask is already reset (sigprocmask()).
	 * 4. There are no environment variables that might niegatively impact
	 *    daemon runtime. */

	int pipe_fd[2], ret;
	pid_t pid;

	/* Pipe for signaling success or failure of daemon creation. See 14. */
	if (pipe(pipe_fd) < 0)
		ERR("pipe");

	/* 5. First fork(). */
	if ((pid = fork()) < 0) {
		ERR("fork");
	} else if (pid) {
		/* Don't need to write to pipe. Read daemon status. */
		if (TEMP_FAILURE_RETRY(close(pipe_fd[1])) < 0)
			ERR("close");
		/* Wait for daemon creation success or failure. */
		if (bulk_read(pipe_fd[0], (char*)&ret, sizeof(ret)) < 0)
			ERR("read from pipe");
		if (TEMP_FAILURE_RETRY(close(pipe_fd[0])) < 0)
			ERR("close");
		/* 15. Exit if daemon was created successfully. */
		if (!ret) {
			closelog();
			exit(EXIT_SUCCESS);
		}
	} else {
		first_child_work(pipe_fd[1], pid_fpath, pid_fd);
		ret = 0;
	}
	return ret;
}
