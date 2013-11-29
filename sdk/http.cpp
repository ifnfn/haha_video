#include <string.h>
#include <curl/curl.h>
#include <curl/easy.h>
#include <syslog.h>

#include "http.hpp"

char * curlGetCurlURL(const char *, struct curl_buffer *, CURL *);
char * curlPostCurlURL(const char *, struct curl_buffer *, CURL *, const char *);

void curl_buffer_free(struct curl_buffer *buf)
{
	if (buf && buf->size > 0 && buf->mem != NULL) {
		free(buf->mem);
	}
}

static void * curlRealloc(void *ptr, size_t size)
{
	if (ptr)
		return realloc(ptr, size);
	else
		return malloc(size);
}

static size_t curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data)
{
	size_t realsize = size * nmemb;
	struct curl_buffer *mem = (struct curl_buffer *)data;

	mem->mem = (char*)curlRealloc(mem->mem, mem->size + realsize + 1);
	if (mem->mem) {
		memcpy( &(mem->mem[mem->size]), ptr, realsize );
		mem->size += realsize;
		mem->mem[mem->size] = 0;
	}
	return realsize;
}

char *http_post(const char *url, const char *body, const char *cookie, const char *referer, struct curl_buffer *curlData)
{
	CURL * curl;

	curl_global_init(CURL_GLOBAL_ALL);
	curl = curl_easy_init();
	if ( !curl ) {
		syslog(LOG_ERR, "wget: cant initialize curl!");
		return NULL;
	}
	
	curl_easy_setopt(curl, CURLOPT_REFERER, referer);
	curl_easy_setopt(curl, CURLOPT_COOKIE, cookie);
	char *memptr = curlPostCurlURL(url, curlData, curl, body);
	curl_easy_cleanup(curl);
	curl_global_cleanup();

	return memptr;
}

char *http_get(const char *url, const char *cookie, const char *referer, struct curl_buffer *curlData)
{
	CURL * curl;

	curl_global_init(CURL_GLOBAL_ALL);
	curl = curl_easy_init();
	if ( !curl ) {
		syslog(LOG_ERR, "wget: cant initialize curl!");
		return NULL;
	}
	curl_easy_setopt(curl, CURLOPT_REFERER, referer);
	curl_easy_setopt(curl, CURLOPT_COOKIE, cookie);

	char * memptr = curlGetCurlURL(url, curlData, curl);
	curl_easy_cleanup(curl);
	curl_global_cleanup();

	return memptr;
}

char * curlGetCurlURL(const char *url, struct curl_buffer *curlData, CURL * curl)
{
	char     errormsg[CURL_ERROR_SIZE];
	CURLcode res;

	curlData->mem  = NULL;
	curlData->size = 0;

	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_ERRORBUFFER, errormsg);
	// curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
	curl_easy_setopt(curl, CURLOPT_USERAGENT, "nntpswitch-libcurl/1.0");
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWriteCallback);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)curlData);

	res = curl_easy_perform(curl);
	if ( res ) {
		syslog(LOG_ERR, "curlGetCurlURL: cant perform curl: %s", errormsg);
		return NULL;
	}
	if ( ! curlData->mem ) {
		syslog(LOG_ERR, "curlGetCurlURL: cant perform curl empty response");
		return NULL;
	}

	return curlData->mem;
}

char * curlPostCurlURL(const char *url, struct curl_buffer *curlData, CURL * curl, const char *postdata)
{
	curl_easy_setopt(curl, CURLOPT_POST, 1);
	curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postdata);

	return curlGetCurlURL(url, curlData, curl);
}
