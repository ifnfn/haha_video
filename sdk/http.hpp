#ifndef _HTTP_HPP_
#define _HTTP_HPP_

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

struct curl_buffer {
	char *mem;
	size_t size;
};

void curl_buffer_free(struct curl_buffer *buffer);
char *http_get (const char *url, const char *cookie, const char *referer, struct curl_buffer *curlData);
char *http_post(const char *url, const char *body, const char *cookie, const char *referer, struct curl_buffer *curlData);


#endif

