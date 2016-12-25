/** \file
 * Implementation of handling server-specific security issues.
 */
#include <string.h>
#include <syslog.h>

#include <openssl/err.h>
#include <openssl/ssl.h>

#include "security.h"

#include "common/misc.h"
#include "common/security.h"

#define MAX_SSL_ACCEPT_RETRIES		5

/**
 * Callback for `SSL_CTX_set_default_passwd_cb` function.
 */
static int pem_passwd_cb(char *buf, int size, int rwflag, void *userdata) {
	UNUSED(rwflag);
	strncpy(buf, (char*)userdata, size);
	buf[size - 1] = '\0';
	return strlen(buf);
}

/**
 * Initialize SSL context using settings read from \p config.
 *
 * See examples:
 * - https://svn.forgerock.org/openam/trunk/opensso/products/webagents/am/source/connection.cpp
 * - http://stackoverflow.com/questions/33265014/openssl-communication-between-client-and-server
 */
int init_ssl_ctx(security_config_t *config) {
	SSL_load_error_strings();
	SSL_library_init();
	OpenSSL_add_all_algorithms(); /* \todo Specify used algorithms only */

	if (ERR_peek_error()) {
		syslog_ssl_err("OpenSSL_add_all_algorithms()");
		goto cleanup_strings;
	}

	config->ssl_method = SSLv23_method();
	config->ssl_ctx = SSL_CTX_new(config->ssl_method);

	if (!config->ssl_ctx) {
		syslog_ssl_err("SSL_CTX_new()");
		goto cleanup_evp;
	}

	/* Limit set of connection methods to most secure + regenerate
	 * Diffie-Hellman key during each handshake. Note that SSL_OP_NO_SSLv2
	 * option is set by default.
	 */
	SSL_CTX_set_options(config->ssl_ctx, SSL_OP_NO_SSLv3 | SSL_OP_SINGLE_DH_USE);

	SSL_CTX_set_cipher_list(config->ssl_ctx, CIPHER_LIST);

	if (!SSL_CTX_set_ecdh_auto(config->ssl_ctx, 1)) {
		syslog_ssl_err("SSL_CTX_set_ecdh_auto()");
		goto cleanup_ctx;
	}

	/** \todo Introduce client's certificate verification. See:
	  * SSL_get_verify_result() and example in SSL_get_verify_result()
	  * manual.
	  */
	SSL_CTX_set_verify(config->ssl_ctx, SSL_VERIFY_NONE, NULL);
	/** SSL_CTX_load_verify_locations(config->ssl_ctx, ca_file, NULL) */

	/** \todo Consider using `SSL_CTX_set_mode()` with probably useful
	 * options, e.g.: SSL_MODE_AUTO_RETRY and SSL_MODE_ENABLE_PARTIAL_WRITE.
	 */

	if (SSL_CTX_use_certificate_chain_file(config->ssl_ctx,
					       config->certificate_path) != 1) {
		syslog_ssl_err("Can't load PEM certificate chain file");
		goto cleanup_ctx;
	}

	SSL_CTX_set_default_passwd_cb_userdata(config->ssl_ctx, (void*)config->private_key_pass);
	SSL_CTX_set_default_passwd_cb(config->ssl_ctx, pem_passwd_cb);

	if (SSL_CTX_use_PrivateKey_file(config->ssl_ctx, config->private_key_path, SSL_FILETYPE_PEM) != 1) {
		syslog_ssl_err("Can't load private key, make sure that you "
			       "provided correct password protecting private key");
		goto cleanup_ctx;
	}

	if (SSL_CTX_check_private_key(config->ssl_ctx) != 1) {
		syslog_ssl_err("Private key doesn't match server's certificate");
		goto cleanup_ctx;
	}

	return 0;

cleanup_ctx:
	SSL_CTX_free(config->ssl_ctx);
cleanup_evp:
	EVP_cleanup();
	if (ERR_peek_error())
		syslog_ssl_err("EVP_cleanup()");
cleanup_strings:
	ERR_free_strings();

	return -1;
}

int accept_client_handshake(SSL *ssl, int socket) {
	int ret, retries;

	syslog(LOG_DEBUG, "Waiting for client's SSL handshake...");

	for (retries = 0; retries < MAX_SSL_ACCEPT_RETRIES; retries++) {
		if ((ret = SSL_accept(ssl)) == 1) {
			syslog(LOG_INFO, "Client's SSL handshake accepted successfully");
			return 0;
		} else if (ret) {
			syslog_ssl_err("SSL_accept() has failed and "
				       "connection shut down was not clean");
		} else {
			syslog_ssl_err("SSL_accept() has failed but was shut "
				       "down with respect to SSL specification");
		}

		if ((ret = handle_ssl_error_want(ret, ssl, socket)) < 0) {
			syslog(LOG_ERR, "Trying to handle SSL_accept() error has failed");
			return -1;
		}
	}

	if (retries >= MAX_SSL_ACCEPT_RETRIES)
		syslog(LOG_ERR, "Maximum number %d of SSL_accept() retries "
		       "reached, giving up", MAX_SSL_ACCEPT_RETRIES);

	return -1;
}
