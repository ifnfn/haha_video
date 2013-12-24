#include <string.h>
#include <syslog.h>
#include <ctype.h>

#include "http.hpp"

inline static unsigned char toHex(unsigned char x)
{
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

static curl_version_info_data *curlinfo = NULL;
void HttpInit()
{
	static int curl_init = 0;
	if (curl_init == 0) {
		curl_global_init(CURL_GLOBAL_ALL);
		curlinfo = curl_version_info(CURLVERSION_NOW);
		curl_init++;
	}
}

void HttpCleanup()
{
	curl_global_cleanup();
}

Http::Http(const char *url)
{
	download_cancel = 0;
	msg = CURLMSG_NONE;

	HttpInit();
	curl = curl_easy_init();

	if ( curl ) {
		SetOpt(CURLOPT_NOSIGNAL        , 1L);
		SetOpt(CURLOPT_TIMEOUT         , 5);
		SetOpt(CURLOPT_CONNECTTIMEOUT  , 5);
		SetOpt(CURLOPT_USERAGENT       , "KolaClient");
		SetOpt(CURLOPT_ERRORBUFFER     , errormsg);

		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWriteCallback);
		curl_easy_setopt(curl, CURLOPT_WRITEDATA    , (void*)this);
		if (curlinfo->features & CURL_VERSION_LIBZ)
			SetOpt(CURLOPT_ACCEPT_ENCODING , "gzip,deflate");

		if (url && strlen(url) > 0)
			SetOpt(CURLOPT_URL, url);
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
	if (url && strlen(url) > 0)
		SetOpt(CURLOPT_URL, url);

	SetCookie(cookie);
	SetReferer(referer);
}

size_t Http::curlWriteCallback(void *ptr, size_t size, size_t nmemb, void *data)
{
	struct Http *http = (Http*)data;

	if (http->download_cancel == 1)
		return 0;

	return http->buffer.write(ptr, size, nmemb);
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
	curl_multi_add_handle(multi_handle, http->curl);
	httpList.push_back(http);
}

void MultiHttp::Remove(Http *http)
{
	curl_multi_remove_handle(multi_handle, http->curl);
	for (deque<Http*>::iterator it = httpList.begin(); it != httpList.end(); it++) {
		if (*it == http) {
			httpList.erase(it);
			break;
		}
	}
}

void MultiHttp::Run()
{
	CURLMsg *msg;  /*  for picking up messages with the transfer status */
	int msgs_left; /*  how many messages are left */

	/*  we start some action by calling perform right away */
	curl_multi_perform(multi_handle, &still_running);

	do {
		struct timeval timeout;
		int rc; /*  select() return code */

		fd_set fdread;
		fd_set fdwrite;
		fd_set fdexcep;
		int maxfd = -1;

		long curl_timeo = -1;

		FD_ZERO(&fdread);
		FD_ZERO(&fdwrite);
		FD_ZERO(&fdexcep);

		/*  set a suitable timeout to play around with */
		timeout.tv_sec = 1;
		timeout.tv_usec = 0;

		curl_multi_timeout(multi_handle, &curl_timeo);
		if(curl_timeo >= 0) {
			timeout.tv_sec = curl_timeo / 1000;
			if(timeout.tv_sec > 1)
				timeout.tv_sec = 1;
			else
				timeout.tv_usec = (curl_timeo % 1000) * 1000;
		}

		/*  get file descriptors from the transfers */
		curl_multi_fdset(multi_handle, &fdread, &fdwrite, &fdexcep, &maxfd);

		/*  In a real-world program you OF COURSE check the return code of the
		 *  function calls.  On success, the value of maxfd is guaranteed to be
		 *  greater or equal than -1.  We call select(maxfd + 1, ...), specially in
		 *  case of (maxfd == -1), we call select(0, ...), which is basically equal
		 *  to sleep. */

		rc = select(maxfd+1, &fdread, &fdwrite, &fdexcep, &timeout);

		switch(rc) {
			case -1:
				/*  select error */
				break;
			case 0: /*  timeout */
			default: /*  action */
				curl_multi_perform(multi_handle, &still_running);
				break;
		}
	} while(still_running);

	/*  See how the transfers went */
	while ((msg = curl_multi_info_read(multi_handle, &msgs_left))) {
		if (msg->msg == CURLMSG_DONE) {
            int found = 0;

			/*  Find out which handle this message is about */
			for (deque<Http*>::iterator it = httpList.begin(); it != httpList.end(); it++) {
				Http *http = *it;

				found = msg->easy_handle == http->curl;

				if(found) {
					http->msg = msg->msg;
					break;
				}
			}

			curl_multi_remove_handle( multi_handle, msg->easy_handle);
		}
	}
}
