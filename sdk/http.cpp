#include <string.h>
#include <syslog.h>

#include "http.hpp"

static char *curlGetCurlURL (const char *, struct curl_buffer *, CURL *);
static char *curlPostCurlURL(const char *, struct curl_buffer *, CURL *, const char *);

struct curl_buffer *curl_buffer_new(void)
{
	return (struct curl_buffer*)calloc(sizeof(struct curl_buffer), 1);
}

std::string uri_join(const char * base, const char * uri)
{
	int location_len;
	const char *p, *path;
	char *buffer = NULL;

	if (strstr(uri, "://"))
		return uri;

	p = strstr(base, "://");
	if (!p)
		return NULL;

	if (strlen(uri) == 0)
		return base;

	p += 3;
	while (*p && *p != '/')
		p++;

	path = p;
	location_len = path - base;

	if (uri[0] == '/') {
		asprintf(&buffer, "%.*s%s", location_len, base, uri);
	} else {
		int path_len;

		p = strrchr (path, '/');
		if (!p)
			path_len = 0;
		else
			path_len = p - path;

		asprintf(&buffer, "%.*s/%s", location_len + path_len, base, uri);
	}

	std::string ret = buffer;
	free(buffer);

	return ret;
}

static void curl_head_init(CURL *curl, const char *referer, const char *cookie)
{
//	curl_version_info_data *curlinfo = curl_version_info(CURLVERSION_NOW);

//	if (curlinfo == NULL)
//		return;

//	curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
//	curl_easy_setopt(curl, CURLOPT_HTTP_VERSION, CURL_HTTP_VERSION_1_1);
//	if (curlinfo->features & CURL_VERSION_LIBZ)
		curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "gzip,deflate");
	curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
	curl_easy_setopt(curl, CURLOPT_TIMEOUT, 3);
	curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 5);
	curl_easy_setopt(curl, CURLOPT_USERAGENT , "KolaClient");
	if (referer)
		curl_easy_setopt(curl, CURLOPT_REFERER, referer);
	if (cookie)
		curl_easy_setopt(curl, CURLOPT_COOKIE, cookie);
}

void curl_buffer_free(struct curl_buffer *buf)
{
	if (buf) {
		if( buf->size > 0 && buf->mem != NULL)
			free(buf->mem);

		free(buf);
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

	curl = curl_easy_init();
	if ( !curl ) {
		syslog(LOG_ERR, "wget: cant initialize curl!");
		return NULL;
	}
	
	curl_head_init(curl, referer, cookie);
	char *memptr = curlPostCurlURL(url, curlData, curl, body);
	curl_easy_cleanup(curl);

	return memptr;
}

char *http_get(const char *url, const char *cookie, const char *referer, struct curl_buffer *curlData)
{
	CURL * curl;

	curl = curl_easy_init();
	if ( !curl ) {
		syslog(LOG_ERR, "wget: cant initialize curl!");
		return NULL;
	}

	curl_head_init(curl, referer, cookie);

	char * memptr = curlGetCurlURL(url, curlData, curl);
	curl_easy_cleanup(curl);

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
