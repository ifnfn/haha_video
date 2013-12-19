#ifndef _HTTP_HPP_
#define _HTTP_HPP_

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <curl/curl.h>
#include <curl/easy.h>
#include <string>
#include <vector>

std::string URLencode(const char *str);
std::string URLdecode(char *str);

std::string uri_join(const char * base, const char * uri);

class HttpBuffer {
	public:
		HttpBuffer():mem(NULL), size(0) {}
		HttpBuffer(HttpBuffer &buf) {
			mem = NULL;
			size  = 0;
			if (buf.size && buf.mem) {
				size = buf.size;
				mem = (char*)malloc(size);
				memcpy(mem, buf.mem, size);
			}
		}

		~HttpBuffer() {
			if (mem) free(mem);
		}

		void init() {
			if (mem) free(mem);

			mem = NULL;
			size  = 0;
		}
		size_t write(void *ptr, size_t size, size_t nmemb);
		char *mem;
		size_t size;
};

void HttpInit();
void HttpCleanup();

class Http {
	public:
		Http();
		~Http();

		void Set(const char *url, const char *cookie=NULL, const char *referer=NULL);
		void SetOpt(CURLoption option, const char *value) { curl_easy_setopt(curl, option, value); }
		void SetOpt(CURLoption option, int value)         { curl_easy_setopt(curl, option, value); }

		bool Get(const char *url, const char *cookie=NULL, const char *referer=NULL);
		char *Post(const char *url, const char *postdata, const char *cookie=NULL, const char *referer=NULL);

		HttpBuffer& Data() { return buffer; }
		HttpBuffer buffer;
	private:
		CURL *curl;
		char *curlGetCurlURL();
		char errormsg[CURL_ERROR_SIZE];
};

class MultiHttp: public std::vector <Http*> {
	public:


};

#endif

