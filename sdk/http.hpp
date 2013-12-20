#ifndef _HTTP_HPP_
#define _HTTP_HPP_

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <curl/curl.h>
#include <curl/easy.h>
#include <string>
#include <deque>

using namespace std;

string UrlEncode(const string& url);
string UrlDecode(const string& sIn);
void HttpInit();
void HttpCleanup();

class HttpBuffer {
	public:
		HttpBuffer():mem(NULL), size(0) {}
		HttpBuffer(HttpBuffer &buf);

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

class Http {
	public:
		Http(const char *url=NULL);
		~Http();

		void Set(const char *url, const char *cookie=NULL, const char *referer=NULL);
		void SetCookie(const char *cookie);
		void SetReferer(const char *referer);

		const char *Get(const char *url=NULL);
		const char *Post(const char *url, const char *postdata);

		void SetOpt(CURLoption option, const char *value) { curl_easy_setopt(curl, option, value); }
		void SetOpt(CURLoption option, int value)         { curl_easy_setopt(curl, option, value); }

		HttpBuffer& Data() { return buffer; }
		HttpBuffer buffer;
		void Cancel();
		int download_cancel;
		CURLMSG msg;
	private:
		CURL *curl;
		char *curlGetCurlURL(int times=0);
		char errormsg[CURL_ERROR_SIZE];
		static size_t curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data);
		friend class MultiHttp;
};

class MultiHttp {
	public:
		MultiHttp();
		~MultiHttp();
		void Add(Http *http);
		void Remove(Http *http);
		void Run();
	private:
		CURLM *multi_handle;
		int still_running;
		deque<Http*> httpList;
};

#endif

