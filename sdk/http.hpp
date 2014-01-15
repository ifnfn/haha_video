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

#include "kola.hpp"
#include "threadpool.hpp"

using namespace std;

string UrlEncode(const string& url);
string UrlDecode(const string& sIn);

class Curl {
	public:
		~Curl();
		static Curl* Instance(void);
		CURL *GetCurl(const char *url);
	private:
		Curl();
		static void my_lock(CURL *handle, curl_lock_data data, curl_lock_access laccess, void *useptr) {
			Curl *user = (Curl *)useptr;
			pthread_mutex_lock(&user->lock);
		}

		static void my_unlock(CURL *handle, curl_lock_data data, void *useptr) {
			Curl *user = (Curl *)useptr;
			pthread_mutex_unlock(&user->lock);
		}

		pthread_mutex_t lock;
		curl_version_info_data *curlinfo;
		CURLSH *share_handle;
};

class HttpBuffer {
	public:
		HttpBuffer():mem(NULL), size(0) {}
		HttpBuffer(HttpBuffer &buf);

		~HttpBuffer() {
			if (mem) free(mem);
		}

		void reset() {
			if (mem) free(mem);

			mem = NULL;
			size  = 0;
		}
		size_t write(void *ptr, size_t size, size_t nmemb);
		char *mem;
		size_t size;
};

class HttpHeader {
public:
	HttpHeader(): Date(0), Expires(0) {}
	time_t Date;
	time_t Expires;
	time_t GetExpiryTime() {
		if (Expires != 0)
			return Expires;
		else
			return Date + 60 * 60 * 24;
	}
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
		long status;
		HttpHeader Headers;
		string url;
		int httpcode;
	private:
		CURL *curl;
		const char *curlGetCurlURL(int times=0);
		char errormsg[CURL_ERROR_SIZE];
		static size_t curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data);
		static size_t curlHeaderCallbck(void *ptr, size_t size, size_t nmemb, void *data);
		friend class MultiHttp;
};

class MultiHttp {
	public:
		MultiHttp();
		~MultiHttp();
		void Add(Http *http);
		void Remove(Http *http);
		void Exec();
	private:
		CURLM *multi_handle;
		int still_running;
		Mutex mutex;
};

#endif

