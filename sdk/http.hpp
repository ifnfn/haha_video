#ifndef HTTP_HPP
#define HTTP_HPP

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <curl/curl.h>
#include <curl/easy.h>
#include <string>
#include <deque>
#include <pthread.h>

using namespace std;

class Mutex;

class Curl {
public:
	~Curl();
	static Curl* Instance(void);
	CURL *GetCurl();
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

	~HttpBuffer();

	void reset();
	bool SaveToFile(const string filename);
	string GetMD5();

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
	Http();
	~Http();

	bool Open(const char *url, const char *cookie=NULL, const char *referer=NULL);
	void Close();
	void SetCookie(const char *cookie);
	void SetReferer(const char *referer);

	const char *Get(const char *url=NULL);
	const char *Post(const char *url, const char *postdata);

	void SetOpt(CURLoption option, void *value);
	void SetOpt(CURLoption option, const char *value);
	void SetOpt(CURLoption option, int value);

	virtual void Progress(curl_off_t dltotal, curl_off_t dlnow, curl_off_t ultotal, curl_off_t ulnow) {
//		printf("HTTP: %lld / %lld (%g %%)\n", dlnow, dltotal, dlnow * 100.0 / dltotal);
	}

	HttpBuffer& Data() { return buffer; }
	HttpBuffer buffer;
	void Cancel();

	int        cancel;
	CURLMSG    msg;
	long       status;
	HttpHeader Headers;
	string     url;
	int        httpcode;
private:
	CURL *curl;
	const char *curlGetCurlURL(int times=0);
	char errormsg[CURL_ERROR_SIZE];
	static size_t curlWriteCallback   (void *ptr, size_t size, size_t nmemb, void *data);
	static size_t curlHeaderCallbck   (void *ptr, size_t size, size_t nmemb, void *data);
	static int    curlProgressCallback(void *data, double dltotal, double dlnow, double ultotal, double ulnow);
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
	Mutex *mutex;
	int work();
};

#endif

