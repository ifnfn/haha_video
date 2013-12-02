#include <string.h>
#include <curl/curl.h>
#include <curl/easy.h>
#include <syslog.h>

#include "http.hpp"

static char *curlGetCurlURL (const char *, struct curl_buffer *, CURL *);
static char *curlPostCurlURL(const char *, struct curl_buffer *, CURL *, const char *);

char *uri_join(const char * base, const char * uri)
{
	int location_len;
	const char *p, *path;
	char *ret = NULL;

	if (strstr(uri, "://"))
		return strdup(uri);

	p = strstr (base, "://");
	if (!p)
		return NULL;

	if (strlen(uri) == 0)
		return strdup(base);

	p += 3;
	while (*p && *p != '/')
		p++;

	path = p;
	location_len = path - base;

	if (uri[0] == '/') {
		asprintf(&ret, "%.*s%s", location_len, base, uri);
	} else {
		int path_len;

		p = strrchr (path, '/');
		if (!p)
			path_len = 0;
		else
			path_len = p - path;

		asprintf(&ret, "%.*s/%s", location_len + path_len, base, uri);
	}

	return ret;
}

static void curl_head_init(CURL *curl, const char *referer, const char *cookie)
{
//	curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
	curl_easy_setopt(curl, CURLOPT_HTTP_VERSION, CURL_HTTP_VERSION_1_1);
	curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "gzip,deflate");
	curl_easy_setopt(curl, CURLOPT_USERAGENT      , "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0");
	if (referer)
		curl_easy_setopt(curl, CURLOPT_REFERER, referer);
	if (cookie)
		curl_easy_setopt(curl, CURLOPT_COOKIE, cookie);
#if 0
	struct curl_slist *headers = NULL;

	headers = curl_slist_append(headers, "HTTP/1.1");
	headers = curl_slist_append(headers, "User-agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0");
	headers = curl_slist_append(headers, "Content-Type: application/x-www-form-urlencoded;charset=UTF-8");
	headers = curl_slist_append(headers, "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
	headers = curl_slist_append(headers, "Accept-Encoding: gzip,deflate");
	headers = curl_slist_append(headers, "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7");
	headers = curl_slist_append(headers, "Connection: Kepp-Alive");

	curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
#endif
}

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
	
	curl_head_init(curl, referer, cookie);
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

	curl_head_init(curl, referer, cookie);

	char * memptr = curlGetCurlURL(url, curlData, curl);
	curl_easy_cleanup(curl);
	curl_global_cleanup();

	return memptr;
}

static char *curlGetCurlURL(const char *url, struct curl_buffer *curlData, CURL * curl)
{
	char     errormsg[CURL_ERROR_SIZE];
	CURLcode res;

	curlData->mem  = NULL;
	curlData->size = 0;

	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_ERRORBUFFER, errormsg);
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

static char *curlPostCurlURL(const char *url, struct curl_buffer *curlData, CURL * curl, const char *postdata)
{
	curl_easy_setopt(curl, CURLOPT_POST, 1);
	curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postdata);

	return curlGetCurlURL(url, curlData, curl);
}
