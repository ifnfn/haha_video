#ifndef __MPEG4IP_HTTP_H__
#define __MPEG4IP_HTTP_H__

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>


typedef struct http_client_ http_client_t;

/*
 * http_resp_t - everything you should need to know about the response
 */
typedef struct http_resp_t {
	int ret_code;
	const char *content_type;
	const char *resp_phrase; // After the response code, a phrase may occur
	const char *xsrf_cookie;
	char *body;
	uint32_t body_len;
} http_resp_t;

#ifdef __cplusplus
extern "C" {
#endif

	/*
	 * http_init_connection - start with this - create a connection to a
	 * particular destination.
	 */
	http_client_t *http_init_connection(const char *url);
	/*
	 * http_free_connection - when done talking to this particular destination,
	 * call this.
	 */
	void http_free_connection(http_client_t *handle);

	/*
	 * http_get - get from a particular url on the location specified above
	 */
	int http_get (http_client_t *, const char *url, http_resp_t **resp, const char *cookie);
	int http_post(http_client_t *cptr,
			const char *url,
			http_resp_t **resp,
			const char *body,
			const char *cookie);
	/*
	 * http_resp_free - free up response structure passed as a result of
	 * http_get
	 */
	void http_resp_free(http_resp_t *);

	/*
	 * http_set_loglevel - set the log level for library output
	 */
	void http_set_loglevel(int loglevel);

	char *URLencode(const char *str);
	char *URLdecode(char *str);
#ifdef __cplusplus
}
#endif

#endif
