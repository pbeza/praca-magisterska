#include <unistd.h>

#include <openssl/err.h>
#include <openssl/ssl.h>

#include "security.h"

#include "common/common.h"
#include "common/security.h"

#define MAX_CONNECTION_RETRY_COUNT	3

/**
 * \todo This initializaiton is simmilar to server's initialization. Make common
 * things common.
 */
int init_ssl_ctx(security_config_t *config) {
	SSL_load_error_strings();
	SSL_library_init();
	OpenSSL_add_all_algorithms();

	if (ERR_peek_error()) {
		syslog_ssl_err("Adding all algorithms probably has failed");
		goto cleanup_strings;
	}

	config->ssl_method = SSLv23_method();
	config->ssl_ctx = SSL_CTX_new(config->ssl_method);

	if (!config->ssl_ctx) {
		syslog_ssl_err("Can't create OpenSSL context");
		goto cleanup_evp;
	}

	SSL_CTX_set_options(config->ssl_ctx, SSL_OP_NO_SSLv3 | SSL_OP_SINGLE_DH_USE);
	/** \todo Add certificate and certificate validation */
	SSL_CTX_set_verify(config->ssl_ctx, SSL_VERIFY_NONE, NULL);

	return 0;

cleanup_evp:
	EVP_cleanup();
	if (ERR_peek_error())
		syslog_ssl_err("EVP_cleanup() probably has failed");
cleanup_strings:
	ERR_free_strings();

	return -1;
}

int cleanup_ssl_ctx(security_config_t *config) {
	int ret = 0;
	SSL_CTX_free(config->ssl_ctx);
	EVP_cleanup();
	if (ERR_peek_error()) {
		syslog_ssl_err("EVP_cleanup() probably has failed");
		ret = -1;
	}
	ERR_free_strings();
	return ret;
}

int start_ssl_handshake(int socket, SSL *ssl) {
	int ret, retries;

	for (retries = 0; retries < MAX_CONNECTION_RETRY_COUNT; retries++) {
		if ((ret = SSL_connect(ssl)) == 1) {
			syslog(LOG_DEBUG, "SSL_connect() success");
			return 0;
		} else if (ret) {
			syslog_ssl_err("SSL_connect() has failed and "
				       "connection shut down was not clean");
		} else {
			syslog_ssl_err("SSL_connect() has failed but was shut "
				       "down with respect to SSL specification");
		}

		if (handle_ssl_error_want(ret, ssl, socket) < 0) {
			syslog(LOG_ERR, "Handling SSL connection error has failed");
			return -1;
		}
	}

	if (retries >= MAX_CONNECTION_RETRY_COUNT)
		syslog(LOG_ERR, "Maximum number %d of SSL_connect() retries "
		       "reached, giving up", MAX_CONNECTION_RETRY_COUNT);

	return -1;
}
