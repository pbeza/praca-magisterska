/** \file
 * Common daemonization process, implemented with respect to the `daemon(7)`
 * manual. For now only SysV traditional daemon is supported.
 * \todo Implement systemd daemon support.
 */
#ifndef _DAEMONIZE_H
#define _DAEMONIZE_H

/**
 * Daemonize current process with respect to `daemon(7)` SysV manual.
 *
 * \param[in] pid_fpath Path to file with daemon's PID to ensure that at most
 * only one instance of daemon can be running.
 * \param[out] pid_fd File descriptor of the \p pid_fpath.
 */
int sysv_daemonize(const char *pid_fpath, int *pid_fd);

#endif
