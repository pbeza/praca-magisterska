#include <syslog.h>

#include <openssl/err.h>
#include <openssl/ssl.h>

#include "security.h"

#include "common/common.h"
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
 * See examples:
 * https://svn.forgerock.org/openam/trunk/opensso/products/webagents/am/source/connection.cpp
 * http://stackoverflow.com/questions/33265014/openssl-communication-between-client-and-server
 */
int init_ssl_ctx(security_config_t *config) {
	SSL_load_error_strings();
	SSL_library_init();
	OpenSSL_add_all_algorithms(); /* \todo Specify only used algorithms */

	/** OpenSSL_add_all_algorithms() can fail - see manual */
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

	/** Limit set of connection methods to most secure + regenerate
	 * Diffie-Hellman key during each handshake. Note that SSL_OP_NO_SSLv2
	 * option is set by default.
	 */
	SSL_CTX_set_options(config->ssl_ctx, SSL_OP_NO_SSLv3 | SSL_OP_SINGLE_DH_USE);

	/** \todo Use only cipers that support Perfect Forward Secrecy. See:
	 * https://www.feistyduck.com/library/openssl-cookbook/online/ch-openssl.html#openssl-cipher-suites-all-together
	 *
	 * SSL_CTX_set_cipher_list(config->ssl_ctx, "CIPHERS_LIST_TODO")
	 */

	/** \todo Introduce client's certificate verification. See:
	  * SSL_get_verify_result() and example in SSL_get_verify_result()
	  * manual.
	  */
	SSL_CTX_set_verify(config->ssl_ctx, SSL_VERIFY_NONE, NULL);
	/** SSL_CTX_load_verify_locations(config->ssl_ctx, ca_file, NULL) */

	/** \todo Consider using `SSL_CTX_set_mode()` with probably useful
	 * options, e.g.: SSL_MODE_AUTO_RETRY and SSL_MODE_ENABLE_PARTIAL_WRITE.
	 *
	 * \todo Manual says that `SSL_CTX_use_certificate_chain_file` should
	 * be preferred.
	 *
	 * \todo Use `SSL_CTX_set_cipher_list`
	 */

	if (SSL_CTX_use_certificate_file(config->ssl_ctx, config->certificate_path, SSL_FILETYPE_PEM) != 1) {
		syslog_ssl_err("Can't load certificate from file");
		goto cleanup_ctx;
	}

	SSL_CTX_set_default_passwd_cb_userdata(config->ssl_ctx, (void*)config->private_key_pass);
	SSL_CTX_set_default_passwd_cb(config->ssl_ctx, pem_passwd_cb);

	if (SSL_CTX_use_PrivateKey_file(config->ssl_ctx, config->private_key_path, SSL_FILETYPE_PEM) != 1) {
		syslog_ssl_err("Can't load private key, make sure that you "
			       "provided correct password protecting private key");
		goto cleanup_ctx;
	}

	/* Check the private against the known certificate */
	if (SSL_CTX_check_private_key(config->ssl_ctx) != 1) {
		syslog_ssl_err("Private key doesn't match server's certificate");
		goto cleanup_ctx;
	}

	return 0;

cleanup_ctx:
	SSL_CTX_free(config->ssl_ctx);
cleanup_evp:
	EVP_cleanup(); /* Can fail - see manual */
	if (ERR_peek_error())
		syslog_ssl_err("EVP_cleanup() probably has failed");
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

int cleanup_ssl_ctx(security_config_t *config) {
	int ret = 0;
	/** \todo See manual if you use SSL_CTX_sess_set_remove_cb() with SSL_CTX_free() */
	SSL_CTX_free(config->ssl_ctx);
	EVP_cleanup(); /* Can fail - see manual */
	if (ERR_peek_error()) {
		syslog_ssl_err("EVP_cleanup() probably has failed");
		ret = -1;
	}
	ERR_free_strings();
	return ret;
}
