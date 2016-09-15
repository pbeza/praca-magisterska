/** \file
 * Functions for daemonizing application with respect to 15 steps introduced by
 * SysV init guide:
 * https://www.freedesktop.org/software/systemd/man/daemon.html#SysV%20Daemons
 */
#include <ctype.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "daemonize.h"
#include "common.h"

/**
 * Access permission bits of the file mode for text file with PID.
 */
#define UNIQ_DAEMON_FILE_PERMISSION	0644

/**
 * Maximum number of digits in PID. This is needed for writing/reading PID
 * to/from `pid_fpath` file.
 */
#define MAX_DIGITS_IN_PID		9

/**
 * This function makes sure that only one instance of daemon is running.
 *
 * \param[in] pid_fpath Path to `flock()`ed text file with daemon's PID.
 * \param[out] fd File descriptor of \p pid_fpath.
 *
 * \return 0 if this is the first daemon running. -1 if daemon is already running.
 */
static int assure_single_daemon_instance(const char *pid_fpath, int *fd) {
	char pid_str[MAX_DIGITS_IN_PID + 1] = { 0 };

	*fd = TEMP_FAILURE_RETRY(open(pid_fpath, O_CREAT | O_RDWR, UNIQ_DAEMON_FILE_PERMISSION));
	if (*fd < 0) {
		syslog_errno("open()");
		return -1;
	}

	/* File locking to allow one daemon instance. Process' exit unlocks it. */
	if (TEMP_FAILURE_RETRY(lockf(*fd, F_TLOCK, 0)) < 0) {
		if (errno != EAGAIN && errno != EACCES)
			syslog_errno("lockf()");
		else
			syslog(LOG_DEBUG, "PID file is already locked");
		goto close_fd;
	}

	snprintf(pid_str, sizeof(pid_str), "%ld", (long)getpid());

	if (bulk_write(*fd, pid_str, strlen(pid_str)) < 0) {
		syslog_errno("bulk_write() can't write PID to file");
		goto close_fd;
	}

	/* DO NOT close() *fd because it would release the file's lock! */
	return 0;

close_fd:
	if (TEMP_FAILURE_RETRY(close(*fd)) < 0)
		syslog_errno("close()");

	return -1;
}

/**
 * Redirects stdin, stdout and stderr to `/dev/null`. This is step no. 9 in
 * `daemon(7)` manual.
 *
 * \return 0 if redirection was successful. -1 otherwise.
 */
static int redirect_to_dev_null() {
	int fd;

	for (fd = 0; fd < 3; fd++)
		if (TEMP_FAILURE_RETRY(close(fd)) < 0) {
			syslog_errno("close()");
			return -1;
		}

	fd = TEMP_FAILURE_RETRY(open("/dev/null", O_RDWR));

	if (fd < 0) {
		syslog_errno("open() for stdin");
		return -1;
	}
	if (dup(fd) < 0) {
		syslog_errno("dup() for stdout");
		goto close_stdin;
	}
	if (dup(fd) < 0) {
		syslog_errno("dup for stderr");
		goto close_stdout;
	}

	return 0;

close_stdout:
	if (TEMP_FAILURE_RETRY(close(fd + 1)) < 0)
		syslog_errno("close()");

close_stdin:
	if (TEMP_FAILURE_RETRY(close(fd)) < 0)
		syslog_errno("close()");

	return -1;
}

/**
 * Work of the daemon after second `fork()` with respect to `daemon(7)` manual.
 */
static int daemon_work(const char *pid_fpath, int *pid_fd) {
	/* 9. Connect stdin, stdout, stderr to /dev/null */
	if (redirect_to_dev_null() < 0) {
		syslog(LOG_ERR, "Redirecting stdin, stdout and stderr to "
		       "/dev/null has failed");
		return -1;
	}

	/* 10. Reset umask to 0. */
	umask(0);

	/* 11. Change the CWD to '/' to avoid that daemon blocks unmounts. */
	if (chdir("/") < 0) {
		syslog_errno("chdir()");
		return -1;
	}

	/* 12. Make sure that other instance of daemon is not working. */
	if (assure_single_daemon_instance(pid_fpath, pid_fd) < 0) {
		syslog(LOG_WARNING, "Another instance of daemon is running");
		return -1;
	}

	return 0;
}

/**
 * Work of the pre-daemon after first `fork()` with respect to `daemon(7)` manual.
 */
static int first_child_work(int pipe_fd[], const char *pid_fpath, int *pid_fd) {
	pid_t pid;
	int ret = -1;

	/* Children don't need to read from pipe. */
	if (TEMP_FAILURE_RETRY(close(pipe_fd[0])) < 0) {
		syslog_errno("close(pipe_fd[0])");
		goto pipe_status;
	}

	/* 6. Detach from any terminal and create an independent session. */
	if (setsid() < 0) {
		syslog_errno("setsid()");
		goto pipe_status;
	}

	/* 7. Second fork() to ensure that the daemon can never re-acquire a
	 * terminal again. */
	if ((pid = fork()) < 0) {
		syslog_errno("fork()");
	} else if (pid) {
		if (TEMP_FAILURE_RETRY(close(pipe_fd[1])) < 0) {
			syslog_errno("close(pipe_fd[1])");
			kill(pid, SIGKILL);
		} else {
			/* 8. Exit in the first child. Ensures reparenting 2nd child. */
			exit(EXIT_SUCCESS);
		}
	} else {
		ret = daemon_work(pid_fpath, pid_fd);
	}

pipe_status:
	/* 13. Dropping privileges is not applicable.
	 * 14. Notify original process that daemon was (un)successfully created. */
	if (bulk_write(pipe_fd[1], (char*)&ret, sizeof(ret)) < 0) {
		syslog(LOG_ERR, "bulk_write() to pipe in daemon");
		ret = -1;
	}

	if (TEMP_FAILURE_RETRY(close(pipe_fd[1])) < 0) {
		syslog_errno("close(pipe_fd[1])");
		ret = -1;
	}

	return ret;
}

/**
 * Work of the parent that made first `fork()` with respect to `daemon(7)` manual.
 * Parent makes blocking `read()` on \p pipe_fd[0] to know whether daemon was
 * created successfully or not.
 *
 * \returns 0 if daemon was created successfully. Otherwise -1.
 */
static int parent_work(int pipe_fd[]) {
	int ret = -1;

	/* Parent don't need to write to pipe. */
	if (TEMP_FAILURE_RETRY(close(pipe_fd[1])) < 0) {
		syslog_errno("close(pipe_fd[1])");
		goto cleanup_read_pipe;
	}

	/* 14. Read daemon status. Wait for daemon creation success/failure. */
	if (bulk_read(pipe_fd[0], (char*)&ret, sizeof(ret)) < 0)
		syslog_errno("bulk_read() from pipe");

cleanup_read_pipe:
	if (TEMP_FAILURE_RETRY(close(pipe_fd[0])) < 0)
		syslog_errno("close(pipe_fd[0])");

	return ret;
}

/**
 * \note To understand why this daemonizing implementation consists of 15 steps
 * enumerated within comments, see `daemon(7)` manual:
 * https://www.freedesktop.org/software/systemd/man/daemon.html#SysV%20Daemons
 *
 * Note that as long as demonization is the first thing we do in program, we can
 * safely assume that:
 *  1. All file descriptors > 3 are closed.
 *  2. All signal handlers are set to their default.
 *  3. Signal mask is already reset (see `man 3p sigprocmask`).
 *  4. There are no environment variables that might negatively impact
 *     daemon runtime.
 *
 * \param[in] pid_fpath Path to file with daemon's PID to ensure that at most
 * only one instance of daemon can be running.
 * \param[out] pid_fd File descriptor of the \p pid_fpath. This file descriptor
 * can't be closed by the process that locked the file as long as we want only
 * one daemon's instance.
 *
 * \return 0 if application was daemonized, ie. it consists of one process
 * running in background. -1 if daemonization wasn't successfull because another
 * daemon instance exists or error has occured.
 */
int sysv_daemonize(const char *pid_fpath, int *pid_fd) {
	pid_t pid;
	int pipe_fd[2], ret = -1;

	/* Pipe for signaling success or failure of daemon creation. See 14. */
	if (pipe(pipe_fd) < 0) {
		syslog_errno("pipe()");
		return -1;
	}

	/* 5. First fork(). */
	if ((pid = fork()) < 0) {
		syslog_errno("fork()");
		if (TEMP_FAILURE_RETRY(close(pipe_fd[0])) < 0 ||
		    TEMP_FAILURE_RETRY(close(pipe_fd[1])) < 0)
			syslog_errno("close() after fork() failure");
	} else if (pid) {
		/* 15. Exit if daemon was created successfully. */
		if (!parent_work(pipe_fd))
			exit(EXIT_SUCCESS);
	} else {
		if ((ret = first_child_work(pipe_fd, pid_fpath, pid_fd)) < 0)
			exit(EXIT_FAILURE);
	}

	return ret;
}
