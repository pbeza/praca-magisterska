/** \file
 * \c UPGRADE_RESPONSE data field compression implementation.
 * Based on: https://github.com/libarchive/libarchive/blob/master/examples/minitar/minitar.c
 */
#include <fcntl.h>
#include <sys/stat.h>
#include <syslog.h>

#include <archive.h>
#include <archive_entry.h>

#include "common/misc.h"
#include "package_archiver.h"

#define ARCHIVE_COPY_BUFFER_LEN		(1 << 14)

static int copy_to_target_archive(struct archive *a,
		struct archive_entry *entry) {

	const char *path = archive_entry_sourcepath(entry);
	char buf[ARCHIVE_COPY_BUFFER_LEN];
	ssize_t len;
	int fd, ret = 0;

	if ((fd = TEMP_FAILURE_RETRY(open(path, O_RDONLY))) < 0) {
		syslog(LOG_ERR, "Failed to open '%s'", path);
		return -1;
	}

	while ((len = bulk_read(fd, buf, ARCHIVE_COPY_BUFFER_LEN)) > 0) {
		if (archive_write_data(a, buf, len) < 0) {
			syslog(LOG_ERR, "archive_write_data() failed, "
					"details: '%s'",
					archive_error_string(a));
			ret = -1;
			break;
		}
	}

	if (len < 0) {
		syslog_errno("Failed to bulk_read() creating archive");
		ret = -1;
	}

	if (TEMP_FAILURE_RETRY(close(fd)) < 0) {
		syslog_errno("Failed to close() file");
		return -1;
	}

	return ret;
}

static int add_to_archive(struct archive *a, const char *path) {
	struct archive *disk;
	struct archive_entry *entry;
	int ret = 0, tmp;

	disk = archive_read_disk_new();
	if (!disk) {
		syslog(LOG_ERR, "archive_read_disk_new() failed, details: '%s'",
				archive_error_string(disk));
		return -1;
	}

	do {
		tmp = archive_read_disk_open(disk, path);
	} while (tmp == ARCHIVE_RETRY);

	if (tmp != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_read_disk_open() failed, details: '%s'",
				archive_error_string(disk));
		ret = -1;
		goto cleanup_archive;
	}

	entry = archive_entry_new();
	if (!entry) {
		syslog(LOG_ERR, "archive_entry_new() failed, "
				"details: '%s'",
				archive_error_string(disk));
		ret = -1;
		goto cleanup_archive;
	}

	while (1) {
		do {
			tmp = archive_read_next_header2(disk, entry);
		} while (tmp == ARCHIVE_RETRY);

		if (tmp == ARCHIVE_EOF) {
			break;
		} else if (tmp != ARCHIVE_OK) {
			syslog(LOG_ERR, "archive_read_next_header2() failed, "
					"details: '%s'",
					archive_error_string(disk));
			ret = -1;
			goto cleanup_archive_all;
		}

		if (archive_read_disk_descend(disk) != ARCHIVE_OK) {
			syslog(LOG_ERR, "archive_read_disk_descend() failed, "
					"details: '%s'",
					archive_error_string(disk));
			ret = -1;
			goto cleanup_archive_all;
		}

		syslog(LOG_DEBUG, "Current archive entry: '%s'",
				archive_entry_pathname(entry));

		do {
			tmp = archive_write_header(a, entry);
		} while (tmp == ARCHIVE_RETRY);

		if (tmp == ARCHIVE_FATAL) {
			syslog(LOG_ERR, "archive_write_header() failed, "
					"details: '%s'",
					archive_error_string(a));
			ret = -1;
			goto cleanup_archive_all;
		} else if (tmp > ARCHIVE_FAILED) { /* ? */
			if (copy_to_target_archive(a, entry) < 0) {
				syslog(LOG_ERR, "Copying to archive failed");
				goto cleanup_archive_all;
			}
		}

		archive_entry_clear(entry);
	}

cleanup_archive_all:
	archive_entry_free(entry);

cleanup_archive:
	do {
		tmp = archive_read_close(a);
	} while (tmp == ARCHIVE_RETRY);

	if (tmp != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_read_close() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
	}

	if (archive_read_free(a) != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_read_free() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
	}

	return ret;
}

int compress(const char *archive_path, compression_type compr_type,
		const char paths[][1024], size_t count) {
	struct archive *a;
	int tmp, ret = 0;
	size_t i;

	a = archive_write_new();
	if (!a) {
		syslog(LOG_ERR, "archive_write_new() failed, details: '%s'",
				archive_error_string(a));
		return -1;
	}

	switch (compr_type) {
		/*case NO_COMPRESSION:*/
		case TAR_GZ_COMPRESSION:
			tmp = archive_write_add_filter_gzip(a);
			break;
		case TAR_BZ2_COMPRESSION:
			tmp = archive_write_add_filter_bzip2(a);
			break;
		case TAR_XZ_COMPRESSION:
			tmp = archive_write_add_filter_xz(a);
			break;
		/*case RAR_COMPRESSION:*/
		case ZIP_COMPRESSION:
			tmp = archive_write_add_filter_lzip(a);
			break;
		default:
			syslog(LOG_ERR, "Unrecognized compression type");
			tmp = ARCHIVE_FATAL;
	}

	if (tmp != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_write_add_filter_*() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
		goto cleanup_archive;
	}

	if (compr_type == ZIP_COMPRESSION)
		tmp = archive_write_set_format_zip(a);
	else
		tmp = archive_write_set_format_ustar(a);

	if (tmp != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_write_set_format_*() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
		goto cleanup_archive;
	}

	if (archive_write_open_filename(a, archive_path) != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_write_open_filename_*() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
		goto cleanup_archive;
	}

	for (i = 0; i < count; i++) {
		add_to_archive(a, paths[i]);
	}

cleanup_archive:
	do {
		tmp = archive_write_close(a);
	} while (tmp == ARCHIVE_RETRY);

	if (tmp != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_write_close() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
	}

	if (archive_write_free(a) != ARCHIVE_OK) {
		syslog(LOG_ERR, "archive_write_free() failed, "
				"details: '%s'", archive_error_string(a));
		ret = -1;
	}

	return ret;
}

int extract(const char *archive_path) {
	UNUSED(archive_path);
	syslog(LOG_ERR, "Extracting is not implemented yet");

	return 0;
}
