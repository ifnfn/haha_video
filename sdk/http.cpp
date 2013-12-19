#include <string.h>
#include <syslog.h>

#include "http.hpp"

static char *curlGetCurlURL (const char *, struct curl_buffer *, CURL *);
static char *curlPostCurlURL(const char *, struct curl_buffer *, CURL *, const char *);

static char _x2c(char hex_up, char hex_low)
{
	char digit;
	digit = 16 * (hex_up >= 'A' ? ((hex_up & 0xdf) - 'A') + 10 : (hex_up - '0'));
	digit += (hex_low >= 'A' ? ((hex_low & 0xdf) - 'A') + 10 : (hex_low - '0'));

	return (digit);
}


/**********************************************
 ** Usage : qURLencode(string to encode);
 ** Return: Pointer of encoded str which is memory allocated.
 ** Do    : Encode string.
 **********************************************/
std::string URLencode(const char *str)
{
	unsigned char c;
	int i, j;
	std::string ret;

	if(str == NULL) return NULL;

	for(i = j = 0; str[i]; i++) {
		c = (unsigned char)str[i];
		if((c >= '0') && (c <= '9')) ret += c;
		else if((c >= 'A') && (c <= 'Z')) ret += c;
		else if((c >= 'a') && (c <= 'z')) ret += c;
		else if((c == '@') || (c == '.') || (c == '/') || (c == '\\')
				|| (c == '-') || (c == '_') || (c == ':') ) ret += c;
		else {
			char buf[4];
			sprintf(buf, "%%%02x", c);
			ret.append(buf);
		}
	}

	return ret;
}

/**********************************************
 ** Usage : qURLdecode(query pointer);
 ** Return: Pointer of query string.
 ** Do    : Decode query string.
 **********************************************/
std::string URLdecode(char *str)
{
	int i, j;

	if(!str) return NULL;
	for(i = j = 0; str[j]; i++, j++) {
		switch(str[j]) {
			case '+':{
					 str[i] = ' ';
					 break;
				 }
			case '%':{
					 str[i] = _x2c(str[j + 1], str[j + 2]);
					 j += 2;
					 break;
				 }
			default:{
					str[i] = str[j];
					break;
				}
		}
	}
	str[i]='\0';

	return str;
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
		return "";

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


static void * curlRealloc(void *ptr, size_t size)
{
	if (ptr)
		return realloc(ptr, size);
	else
		return malloc(size);
}

size_t HttpBuffer::write(void *ptr, size_t s, size_t nmemb)
{
	size_t realsize = s * nmemb;
	mem = (char*)curlRealloc(mem, size + realsize + 1);
	if (mem) {
		memcpy( &(mem[size]), ptr, realsize );
		size += realsize;
		mem[size] = 0;
	}

	return realsize;
}

void HttpInit() {
	static int curl_init = 0;
	if (curl_init == 0) {
		curl_global_init(CURL_GLOBAL_ALL);
		curl_init++;
	}
}

void HttpCleanup() {
	curl_global_cleanup();
}

Http::Http() {
	curl = curl_easy_init();
	if ( curl ) {
		curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "gzip,deflate");
		curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT, 3);
		curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 5);
		curl_easy_setopt(curl, CURLOPT_USERAGENT , "KolaClient");
	}
	else
		syslog(LOG_ERR, "wget: cant initialize curl!");
}

Http::~Http() {
	if (curl)
		curl_easy_cleanup(curl);
}

static size_t curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data)
{
	struct Http *http = (Http*)data;

	return http->buffer.write(ptr, size, nmemb);
}

void Http::Set(const char *url, const char *cookie, const char *referer)
{
	if (referer)
		curl_easy_setopt(curl, CURLOPT_REFERER, referer);
	if (cookie)
		curl_easy_setopt(curl, CURLOPT_COOKIE, cookie);

	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_ERRORBUFFER, errormsg);
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWriteCallback);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)this);
}

char *Http::curlGetCurlURL(int times)
{
	CURLcode res;

	if (times > 3)
		return NULL;

	buffer.init();

	res = curl_easy_perform(curl);
	if ( res ) {
		printf("curlGetCurlURL: cant perform curl: %s", errormsg);
		return curlGetCurlURL(times + 1);
	}

	if (buffer.mem == NULL)
		return curlGetCurlURL(times + 1);

	return buffer.mem;
}

const char *Http::Get(const char *url, const char *cookie, const char *referer)
{
	Set(url, cookie, referer);

	return curlGetCurlURL();
}

const char *Http::Post(const char *url, const char *postdata, const char *cookie, const char *referer)
{
	Set(url, cookie, referer);
	curl_easy_setopt(curl, CURLOPT_POST, 1);
	curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postdata);

	return curlGetCurlURL();
}

