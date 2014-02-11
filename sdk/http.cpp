#include <string.h>
#include <syslog.h>
#include <ctype.h>
#include <pthread.h>

#include "http.hpp"

#define NETWORK_TIMEOUT 10

inline static unsigned char toHex(unsigned char x) {
	return x > 9 ? x + 55 : x + 48;
}

string UrlEncode(const string & sIn)
{
	string sOut;

	for(size_t i=0; i < sIn.size(); ++i) {
		unsigned char buf[4];
		memset(buf, 0, 4);
		if(isalnum((unsigned char)sIn[i]))
			buf[0] = sIn[i];
		else if(isspace((unsigned char)sIn[i]))
			buf[0] = '+';
		else {
			buf[0] = '%';
			buf[1] = toHex((unsigned char)sIn[i] >> 4);
			buf[2] = toHex((unsigned char)sIn[i] % 16);
		}
		sOut += (char *)buf;
	}

	return sOut;
}

string UrlDecode(const string & sIn)
{
	string sOut;

	for(size_t i = 0; i < sIn.size(); i++) {
		unsigned char buf[4];
		memset(buf, 0, 4);
		if( isalnum( sIn[i] ) )
			buf[0] = sIn[i];
		else if ( '+'==( sIn[i] ) )
			buf[0] = ' ';
		else {
			buf[0] = toHex( sIn[i + 1] << 4 );
			buf[1] = toHex( sIn[i]);
		}
		sOut += (char *)buf;
	}

	return sOut;
}

static void *curlRealloc(void *ptr, size_t size)
{
	if (ptr)
		return realloc(ptr, size);
	else
		return malloc(size);
}

HttpBuffer::HttpBuffer(HttpBuffer &buf)
{
	mem = NULL;
	size  = 0;
	if (buf.size && buf.mem) {
		size = buf.size;
		mem = (char*)malloc(size);
		memcpy(mem, buf.mem, size);
	}
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

Curl* Curl::Instance(void)
{
	static Curl _curl;

	return &_curl;
}

Curl::Curl() {
	static int curl_init = 0;
	if (curl_init == 0) {
		pthread_mutex_init(&lock, NULL);
		curl_global_init(CURL_GLOBAL_ALL);
		share_handle = curl_share_init();
		curlinfo = curl_version_info(CURLVERSION_NOW);

		curl_share_setopt(share_handle, CURLSHOPT_SHARE     , CURL_LOCK_DATA_DNS);
		curl_share_setopt(share_handle, CURLSHOPT_LOCKFUNC  , my_lock);
		curl_share_setopt(share_handle, CURLSHOPT_UNLOCKFUNC, my_unlock);
		curl_share_setopt(share_handle, CURLSHOPT_USERDATA  , this);
		curl_init++;
	}
}

Curl::~Curl() {
	curl_share_cleanup(share_handle);
	curl_global_cleanup();
	pthread_mutex_destroy(&lock);
}

CURL *Curl::GetCurl(const char *url) {
	CURL *curl = curl_easy_init();

	if ( curl ) {
		curl_easy_setopt(curl, CURLOPT_NOSIGNAL         , 1L);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT          , NETWORK_TIMEOUT);
		curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT   , NETWORK_TIMEOUT);
		curl_easy_setopt(curl, CURLOPT_USERAGENT        , "KolaClient");
		curl_easy_setopt(curl, CURLOPT_SHARE            , share_handle);
		curl_easy_setopt(curl, CURLOPT_DNS_CACHE_TIMEOUT, 60 * 5);
		if (curlinfo->features & CURL_VERSION_LIBZ)
			curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING , "gzip,deflate");

		if (url && strlen(url) > 0)
			curl_easy_setopt(curl, CURLOPT_URL, url);
	}

	return curl;
}

Http::Http(const char *url)
{
	download_cancel = 0;
	msg = CURLMSG_NONE;
	status = 0;
	httpcode = 0;

	if (url)
		this->url = url;

	curl = Curl::Instance()->GetCurl(url);

	if ( curl) {
		curl_easy_setopt(curl, CURLOPT_ERRORBUFFER     , errormsg);
		curl_easy_setopt(curl, CURLOPT_PRIVATE         , this);

		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION   , curlWriteCallback);
		curl_easy_setopt(curl, CURLOPT_WRITEDATA       , (void*)this);

		curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION  , curlHeaderCallbck);
		curl_easy_setopt(curl, CURLOPT_HEADERDATA      , (void*)this);
	}
	else
		syslog(LOG_ERR, "wget: cant initialize curl!");
}

Http::~Http()
{
	if (curl)
		curl_easy_cleanup(curl);
}

void Http::SetCookie(const char *cookie)
{
	if (cookie && strlen(cookie) > 0)
		SetOpt(CURLOPT_COOKIE, cookie);
}

void Http::SetReferer(const char *referer)
{
	if (referer && strlen(referer) > 0)
		SetOpt(CURLOPT_REFERER, referer);
}

void Http::Set(const char *url, const char *cookie, const char *referer)
{
	if (url && strlen(url) > 0) {
		this->url = url;
		SetOpt(CURLOPT_URL, url);
	}

	SetCookie(cookie);
	SetReferer(referer);
}

size_t Http::curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data)
{
	Http *http = (Http*)data;

	if (http->download_cancel == 1)
		return 0;

	return http->buffer.write(ptr, size, nmemb);
}

size_t Http::curlHeaderCallbck(void *ptr, size_t size, size_t nmemb, void *data)
{
	Http *http = (Http*)data;

	const char *s = (const char *)ptr;

	if (strncmp(s, "HTTP", 4) == 0) {
		int httpversion_major, httpversion;
		sscanf(s, "HTTP/%d.%d %3d", &httpversion_major, &httpversion, &http->httpcode);
	}
	else if (strncmp(s, "Date: ", 6) == 0)
		http->Headers.Date = curl_getdate(&s[6], NULL);
	else if (strncmp(s, "Expires: ", 9) == 0)
		http->Headers.Expires = curl_getdate(&s[9], NULL);

	return size * nmemb;
}

const char *Http::curlGetCurlURL(int times)
{
	CURLcode res;

	if (times > 3)
		return NULL;

	buffer.reset();

	res = curl_easy_perform(curl);
	if ( res ) {
		printf("curlGetCurlURL: %s, cant perform curl: %s\n", url.c_str(), errormsg);
		return curlGetCurlURL(times + 1);
	}

	if (buffer.mem == NULL)
		return curlGetCurlURL(times + 1);

	if (this->httpcode != 200 && this->httpcode != 304) {
		buffer.reset();
		return NULL;
	}

	return buffer.mem;
}

const char *Http::Get(const char *url)
{
	Set(url);

	return curlGetCurlURL();
}

const char *Http::Post(const char *url, const char *postdata)
{
	Set(url);
	SetOpt(CURLOPT_POST, 1);
	SetOpt(CURLOPT_POSTFIELDS, postdata);

	return curlGetCurlURL();
}

void Http::Cancel()
{
	download_cancel = 1;
}

MultiHttp::MultiHttp()
{
	multi_handle = curl_multi_init();
}

MultiHttp::~MultiHttp()
{
	curl_multi_cleanup(multi_handle);
}

void MultiHttp::Add(Http *http)
{
	mutex.lock();
	curl_multi_add_handle(multi_handle, http->curl);
	mutex.unlock();
}

void MultiHttp::Remove(Http *http)
{
	mutex.lock();
	curl_multi_remove_handle(multi_handle, http->curl);
	mutex.unlock();
}

void MultiHttp::Exec()
{
	CURLMsg *msg;  /*  for picking up messages with the transfer status */
	int msgs_left; /*  how many messages are left */
	fd_set fdread;
	fd_set fdwrite;
	fd_set fdexcep;
	struct timeval timeout;

	while (1) {
		int maxfd = -1;
		long curl_timeo = -1;

		FD_ZERO(&fdread);
		FD_ZERO(&fdwrite);
		FD_ZERO(&fdexcep);
		mutex.lock();
		curl_multi_fdset(multi_handle, &fdread, &fdwrite, &fdexcep, &maxfd);

		timeout.tv_sec = 3;
		timeout.tv_usec = 0;
		curl_multi_timeout(multi_handle, &curl_timeo);

		if(curl_timeo >= 0) {
			timeout.tv_sec = curl_timeo / 1000;
			if(timeout.tv_sec > 1)
				timeout.tv_sec = 1;
			else
				timeout.tv_usec = (curl_timeo % 1000) * 1000;
		}

		int rc = select(maxfd+1, &fdread, &fdwrite, &fdexcep, &timeout);

		if (rc < 0) {
			mutex.unlock();
			continue;
		}

		while( curl_multi_perform( multi_handle, &still_running ) == CURLM_CALL_MULTI_PERFORM ) {
			// DEBUG( "TransferThread::Run(): %i transfers still running.\n", nRunning );
		}

		if (still_running == 0)
			break;

		/*  See how the transfers went */
		while ((msg = curl_multi_info_read(multi_handle, &msgs_left))) {
			if (msg->msg == CURLMSG_DONE) {
				Http* http = NULL;
				long ncode;

				curl_easy_getinfo( msg->easy_handle, CURLINFO_PRIVATE, (char**)&http );
				curl_easy_getinfo( msg->easy_handle, CURLINFO_RESPONSE_CODE, &ncode );

				if (http) {
					http->status = ncode;
					http->msg = msg->msg;
				}

				curl_multi_remove_handle( multi_handle, msg->easy_handle);
			}
			else
				printf("TransferThread: Got unknown message code %i from curl_multi_info_read()!\n", msg->msg);
		}
		mutex.unlock();
	}
}
