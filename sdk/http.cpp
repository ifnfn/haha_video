#include <string.h>
#include <syslog.h>
#include <ctype.h>
#include <pthread.h>
#include <openssl/md5.h>

#include "common.hpp"
#include "http.hpp"
#include "kola.hpp"

#define NETWORK_TIMEOUT 15
#define TRY_TIME 1

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

bool HttpBuffer::SaveToFile(const string filename) {
	FILE *fp = fopen(filename.c_str(), "wb");
	if (fp) {
		fwrite(mem, 1, size, fp);
		fclose(fp);

		return true;
	}

	return false;
}

string HttpBuffer::GetMD5()
{
	return MD5(mem, size);
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

CURL *Curl::GetCurl() {
	CURL *curl = curl_easy_init();

	if ( curl ) {
		curl_easy_setopt(curl, CURLOPT_NOSIGNAL         , 1L);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT          , NETWORK_TIMEOUT);
		curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT   , NETWORK_TIMEOUT);
		curl_easy_setopt(curl, CURLOPT_USERAGENT        , "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 Safari/537.36");

		curl_easy_setopt(curl, CURLOPT_SHARE            , share_handle);
		curl_easy_setopt(curl, CURLOPT_DNS_CACHE_TIMEOUT, 60);
		curl_easy_setopt(curl, CURLOPT_BUFFERSIZE       , 1024 * 8);
		if (curlinfo->features & CURL_VERSION_LIBZ)
			curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING , "gzip,deflate");
	}

	return curl;
}

Http::Http()
{
	cancel = 0;
	msg = CURLMSG_NONE;
	status = 0;
	httpcode = 0;
	curl = NULL;
}

Http::~Http()
{
	Close();
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

void Http::SetOpt(CURLoption option, const char *value)
{
	if (curl)
		curl_easy_setopt(curl, option, value);
}

void Http::SetOpt(CURLoption option, int value)
{
	if (curl)
		curl_easy_setopt(curl, option, value);
}


bool Http::Open(const char *url, const char *cookie, const char *referer)
{
	if (curl == NULL)
		curl = Curl::Instance()->GetCurl();

	if ( curl) {
		curl_easy_setopt(curl, CURLOPT_ERRORBUFFER     , errormsg);
		curl_easy_setopt(curl, CURLOPT_PRIVATE         , this);

		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION   , curlWriteCallback);
		curl_easy_setopt(curl, CURLOPT_WRITEDATA       , (void*)this);

		curl_easy_setopt(curl, CURLOPT_HEADERFUNCTION  , curlHeaderCallbck);
		curl_easy_setopt(curl, CURLOPT_HEADERDATA      , (void*)this);

		curl_easy_setopt(curl, CURLOPT_NOPROGRESS      , 0L);
		curl_easy_setopt(curl, CURLOPT_PROGRESSFUNCTION, curlProgressCallback);
		curl_easy_setopt(curl, CURLOPT_PROGRESSDATA    , (void*)this);
		SetCookie(cookie);
		if (url && strlen(url) > 0) {
			this->url = url;
			SetOpt(CURLOPT_URL, url);
		}
		if (referer)
			SetReferer(referer);
		else if (url)
			SetReferer(url);

		return true;
	}
	else
		syslog(LOG_ERR, "wget: cant initialize curl!");

	return false;
}

void Http::Close()
{
	if (curl) {
		curl_easy_cleanup(curl);
		curl = NULL;
	}
}

int Http::curlProgressCallback(void *data, double dltotal, double dlnow, double ultotal, double ulnow)
{
	Http *http = (Http*)data;

	http->Progress((curl_off_t)dltotal, (curl_off_t)dlnow, (curl_off_t)ultotal, (curl_off_t)ulnow);

	return 0;
}

size_t Http::curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data)
{
	Http *http = (Http*)data;

	if (http->cancel == 1)
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
	const char *data = NULL;

	if (times >= TRY_TIME)
		return NULL;

	buffer.reset();

	res = curl_easy_perform(curl);
	if ( res ) {
		printf("curlGetCurlURL: %s, cant perform curl: %s\n", url.c_str(), errormsg);
		if (cancel == 1)
			goto end;
		return curlGetCurlURL(times + 1);
	}

	if (cancel == 1) {
		goto end;
	}

	if (buffer.mem == NULL)
		return curlGetCurlURL(times + 1);

	if (this->httpcode != 200 && this->httpcode != 304) {
		buffer.reset();
		goto end;
	}
	data = buffer.mem;
end:
	status = CURLMSG_DONE;
	return data;
}

const char *Http::Get(const char *url)
{
	const char *data;
	Open(url);

	data = curlGetCurlURL();
	Close();

	return data;
}

const char *Http::Post(const char *url, const char *postdata)
{
	const char *data;
	Open(url);

	SetOpt(CURLOPT_POST, 1);
	SetOpt(CURLOPT_POSTFIELDS, postdata);

	data = curlGetCurlURL();
	Close();

	return data;
}

void Http::Cancel()
{
	cancel = 1;
}

MultiHttp::MultiHttp()
{
	mutex = new Mutex();
	multi_handle = curl_multi_init();
}

MultiHttp::~MultiHttp()
{
	curl_multi_cleanup(multi_handle);
	delete mutex;
}

void MultiHttp::Add(Http *http)
{
	mutex->lock();
	curl_multi_add_handle(multi_handle, http->curl);
	mutex->unlock();
}

void MultiHttp::Remove(Http *http)
{
	mutex->lock();
	curl_multi_remove_handle(multi_handle, http->curl);
	mutex->unlock();
}

void MultiHttp::Exec()
{
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
		mutex->lock();
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
			mutex->unlock();
			continue;
		}

		int still_running = this->work();

		mutex->unlock();

		if (still_running == 0)
			break;
	}
}

int MultiHttp::work()
{
	int msgs_left;
	CURLMsg *msg;
	int still_running;

	while( curl_multi_perform( multi_handle, &still_running ) == CURLM_CALL_MULTI_PERFORM ) {
		// DEBUG( "TransferThread::Run(): %i transfers still running.\n", nRunning );
	}
	while((msg = curl_multi_info_read(multi_handle, &msgs_left))){
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

	return still_running;
}
