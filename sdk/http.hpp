#ifndef _HTTP_HPP_
#define _HTTP_HPP_

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <curl/curl.h>
#include <curl/easy.h>
#include <string>

struct curl_buffer {
	char *mem;
	size_t size;
};

struct curl_buffer *curl_buffer_new(void);
void curl_buffer_free(struct curl_buffer *buffer);
std::string uri_join(const char * base, const char * uri);
char *http_get (const char *url, const char *cookie, const char *referer, struct curl_buffer *curlData);
char *http_post(const char *url, const char *body, const char *cookie, const char *referer, struct curl_buffer *curlData);


#endif

