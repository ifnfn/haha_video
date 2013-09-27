#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <pcre.h>
#include <iostream>
#include <stdexcept>
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <zlib.h>

#include "json.h"
#include "httplib.h"
#include "base64.hpp"
#include "kola.hpp"
#include "pcre.hpp"
#include "threadpool.hpp"

//#define SERVER_HOST "127.0.0.1"
//#define SERVER_HOST "121.199.20.175"
//#define SERVER_HOST "112.124.60.152"
//#define PORT 9991
#define SERVER_HOST "www.kolatv.com"
#define PORT 80

#define MAX_THREAD_POOL_SIZE 8
#define TRY_TIMES 3

static std::string loginKey;
static std::string loginKeyCookie;
static std::string xsrf_cookie;

#if 1
#define LOCK(lock)   pthread_mutex_lock(&lock)
#define UNLOCK(lock) pthread_mutex_unlock(&lock)
#else
#define LOCK(lock)   do {} while(0)
#define UNLOCK(lock) do {} while(0)
#endif

#if ENABLE_SSL

#include <openssl/pem.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/bio.h>
#include <openssl/rsa.h>

static RSA *rsa = NULL;
int Decrypt(int flen, const unsigned char *from, unsigned char *to)
{
	//	return RSA_public_decrypt(flen, from, to, rsa, RSA_PKCS1_PADDING);
}

int Encrypt(int flen, const unsigned char *in, int in_size, unsigned char *out, int out_size)
{
	int rsa_size = RSA_size(rsa);
	int blocks = in_size / rsa_size;
	int cur_len = 0;

	for (int i = 0; i < blocks; i++) {

	}
	//	return RSA_public_encrypt(flen, from, to, rsa, RSA_PKCS1_PADDING);
}
#endif

static char *GetIP(const char *hostp)
{
	char str[32];
	struct hostent *host = gethostbyname(hostp);

	if (host == NULL)
		return NULL;

	inet_ntop(host->h_addrtype, host->h_addr, str, sizeof(str));

	return strdup(str);
}

static char *ReadStringFile(FILE *fp)
{
#define LEN 2048
	char *s = NULL;

	if (fp) {
		long size = 0;
		int len;
		while (1) {
			s = (char *)realloc(s, size + LEN);
			len = fread(s + size, 1, LEN, fp);
			if (len > 0)
				size += len;
			else
				break;
		}
	}

	return s;
}

/* Compress gzip data */
static int gzcompress(Bytef *data, uLong ndata, Bytef *zdata, uLong *nzdata)
{
	z_stream c_stream;
	int err = 0;

	if(data && ndata > 0)
	{
		c_stream.zalloc = Z_NULL;
		c_stream.zfree = Z_NULL;
		c_stream.opaque = Z_NULL;
		if(deflateInit2(&c_stream, Z_DEFAULT_COMPRESSION, Z_DEFLATED,
					-MAX_WBITS, 8, Z_DEFAULT_STRATEGY) != Z_OK) return -1;
		c_stream.next_in  = data;
		c_stream.avail_in  = ndata;
		c_stream.next_out = zdata;
		c_stream.avail_out  = *nzdata;
		while (c_stream.avail_in != 0 && c_stream.total_out < *nzdata)
		{
			if(deflate(&c_stream, Z_NO_FLUSH) != Z_OK) return -1;
		}
		if(c_stream.avail_in != 0) return c_stream.avail_in;
		for (;;) {
			if((err = deflate(&c_stream, Z_FINISH)) == Z_STREAM_END) break;
			if(err != Z_OK) return -1;
		}
		if(deflateEnd(&c_stream) != Z_OK) return -1;
		*nzdata = c_stream.total_out;
		return 0;
	}
	return -1;
}

static std::string gzip_base64(const char *data, int ndata)
{
	std::string ret;
	Byte *zdata = (Byte*)malloc(ndata * 2);
	uLong nzdata = ndata * 2;

	if (gzcompress((Bytef *)data, (uLong)ndata, zdata, &nzdata) == 0) {
		data = (const char*)zdata;
		ndata = nzdata;
	}
	int out_size = BASE64_SIZE(ndata) + 1;

	char *out_buffer = (char *)calloc(1, out_size);
	base64encode((unsigned char *)data, ndata, (unsigned char*)out_buffer, out_size);

	ret = out_buffer;

	delete out_buffer;
	delete zdata;

	return ret;
}

Picture::Picture(std::string fileName) {
	data = NULL;
	size = 0;
	inCache = false;
	Caching();
}

Picture::Picture() {
	data = NULL;
	size = 0;
	inCache = false;
}

Picture::~Picture() {
	if (data)
		free(data);
}

static void *download_thread(void *arg) {
	Picture *pic = (Picture*) pic;
	pic->wget();

	return NULL;
}

bool Picture::wget()
{
	if (inCache)
		return inCache;
	KolaClient *client = &KolaClient::Instance();

	bool ok = false;
	http_resp_t *http_resp = NULL;

	if (client->UrlGet(fileName, "", (void**)&http_resp)) {
		size = http_resp->body_len;
		data = malloc(size);
		memcpy(data, http_resp->body, size);
		inCache = true;
		ok = true;
		printf("size=%d, data=%p\n", size, data);
	}
	http_resp_free(http_resp);

	return ok;
}

// 加入线程池
void Picture::Caching()
{
	KolaClient *client = &KolaClient::Instance();
	pool_add_worker((thread_pool_t)client->threadPool, download_thread, this);
}

KolaMenu::KolaMenu() {
	cid = -1;
	PageId = -1;
	PageSize = 20;

	client = &KolaClient::Instance();
}

KolaMenu::KolaMenu(json_t *js)
{
	PageSize = 20;
	PageId   = -1;
	name = json_gets(js, "name", "");
	cid = json_geti(js, "cid" , -1);
	json_t *filter = json_geto(js, "filter");

	client = &KolaClient::Instance();

	if (filter) {
		const char *key;
		json_t *values;
		json_object_foreach(filter, key, values) {
			json_t *v;
			std::string list;
			json_array_foreach(values, v)
				list = list + json_string_value(v) + ",";
			Filter.filterKey.insert(std::pair<std::string, FilterValue>(key, FilterValue(list)));
		}
	}

	printf("cid = %d, name = %s\n", cid, name.c_str());
}

KolaMenu::KolaMenu(const KolaMenu &m) {
	name = m.name;
	cid = m.cid;
	PageSize = m.PageSize;
	PageId = m.PageId;
	client = m.client;
	Filter = m.Filter;
//	client = &KolaClient::Instance();
}

bool KolaMenu::GetPage(int page)
{
	char url[256];
	int count = 0;
	std::string text;
	std::string body("{");
	std::string filter = Filter.GetJsonStr();
	std::string sort = Sort.GetJsonStr();
	if (filter.size() > 0) {
		count++;
		body = body + filter;
	}
	if (sort.size() > 0) {
		if (count)
			body = body + ",";
		body = body + sort;
	}
	body = body + "}";

	std::cout << "Filter Body: " << body << std::endl;

	if (name == "" or cid == -1)
		return false;
	if (page == -1)
		PageId++;
	else
		PageId = page;

	sprintf(url, "/video/list?page=%d&size=%d&menu=%s", PageId, PageSize, name.c_str());
	if (client->UrlPost(url, body.c_str(), text) == true) {
		clear();

		json_error_t error;
		json_t *js = json_loads(text.c_str(), JSON_REJECT_DUPLICATES, &error);
		if (js) {
			json_t *results = json_geto(js, "result");

			if (results && json_is_array(results)) {
				json_t *value;
				json_array_foreach(results, value)
					push_back(KolaAlbum(value));
			}

//			std::cout << text << std::endl;
			json_delete(js);
		}
	}

	return true;
}

void *kola_login_thread(void *arg);
KolaClient::KolaClient(void)
{
	char buffer[512];
	char *p = GetIP(SERVER_HOST);

	if (p) {
		sprintf(buffer, "http://%s:%d", p, PORT);
		baseUrl = buffer;
		delete p;
	}

	nextLoginSec = 3;
	running = true;

	threadPool = (void*)pool_create(MAX_THREAD_POOL_SIZE);

	pthread_mutex_init(&lock, NULL);
	Login();
	pthread_create(&thread, NULL, kola_login_thread, this);
}

void KolaClient::Quit(void)
{
	pthread_cancel(thread);
	pthread_join(thread, NULL);
	printf("KolaClient Quit: %p\n", this);
}

KolaClient::~KolaClient(void)
{
#if ENABLE_SSL
	if (rsa)
		RSA_free(rsa);
#endif
	pool_free((thread_pool_t)threadPool);
	Quit();
}

bool KolaClient::UrlGet(std::string url, const char *home_url, void **resp, int times)
{
	bool ok = false;
	int rc;
	http_client_t *http_client;
	http_resp_t **http_resp = (http_resp_t **)resp;
	std::string cookie;

	if (times > TRY_TIMES)
		return false;

	if (home_url == NULL)
		home_url = baseUrl.c_str();

	http_client = http_init_connection(home_url);
	if (http_client == NULL) {
		printf("no client: %s\n", url.c_str());
		return false;
	}
	LOCK(lock);
	cookie = loginKeyCookie;
	UNLOCK(lock);

	rc = http_get(http_client, url.c_str(), http_resp, cookie.c_str());
	if (rc && *http_resp && (*http_resp)->body) {
		if ((*http_resp)->xsrf_cookie)
			xsrf_cookie = (*http_resp)->xsrf_cookie;
		ok = true;
	}

	http_free_connection(http_client);

	if (ok == false) {
		http_resp_free(*http_resp);
		return UrlGet(url, home_url, resp, times + 1);
	}
	else
		return ok;
}

bool KolaClient::UrlGet(std::string url, std::string &ret, const char *home_url)
{
	bool ok = false;
	http_resp_t *http_resp = NULL;

	if (UrlGet(url, home_url, (void**)&http_resp)) {
		ret = http_resp->body;
		ok = true;

	}
	http_resp_free(http_resp);

	return ok;
}

bool KolaClient::UrlPost(std::string url, const char *body, std::string &ret, const char *home_url, int times)
{
	bool ok = false;
	int rc;
	http_client_t *http_client;
	http_resp_t *http_resp = NULL;
	std::string cookie, new_body;

	if (times > TRY_TIMES)
		return false;

	if (home_url == NULL)
		home_url = baseUrl.c_str();

	http_client = http_init_connection(home_url);
	if (http_client == NULL) {
		printf("no client: %s\n", url.c_str());
		return false;
	}

	LOCK(lock);
	cookie = loginKeyCookie;
#if 0
	if (xsrf_cookie.size() > 0 && times == 0) {
		if (url.find("?") != std::string::npos)
			url = url + "&" + xsrf_cookie;
		else
			url = url + "?" + xsrf_cookie;
	}
#endif

	UNLOCK(lock);

	new_body = gzip_base64(body, strlen(body));
	rc = http_post(http_client, url.c_str(), &http_resp, new_body.c_str(), cookie.c_str());
	if (rc && http_resp && http_resp->body) {
		ret = http_resp->body;
		ok = true;
	}

	http_resp_free(http_resp);
	http_free_connection(http_client);

	if (ok == false)
		return UrlPost(url, body, ret, home_url, times + 1);
	else
		return ok;
}

void KolaClient::GetKey(void)
{
	std::string text;
	if (UrlGet("/key", text) == true) {
#if ENABLE_SSL
		BIO *key= BIO_new_mem_buf((void*)text.c_str(), text.size());
		rsa = PEM_read_bio_RSA_PUBKEY(key, NULL, NULL, NULL);
		BIO_free_all(key);
#endif
	}
}

char *KolaClient::Run(const char *cmd)
{
	FILE *fp = popen(cmd, "r");
	char *s = ReadStringFile(fp);

	fclose(fp);

	return s;
}

bool KolaClient::ProcessCommand(json_t *cmd, const char *dest)
{
	std::string text;
	Pcre pcre;
	const char *name = json_gets(cmd, "name", "");
	const char *source = json_gets(cmd, "source", "");

//	name = "album";
//	source = "http://tv.sohu.com/s2012/azhx/";
	printf("[%s]: %s --> %s\n", name, source, dest);

	if (UrlGet("", text, source) == false)
		return false;

	if (text.size() == 0)
		return false;

	json_t *regular = json_geto(cmd, "regular");
	if (regular && json_is_array(regular)) {
		json_t *value;

		json_array_foreach(regular, value) {
			const char *r = json_string_value(value);
			pcre.AddRule(r);
		}

		text = pcre.MatchAll(text.c_str());
	}

	json_t *json_filter = json_geto(cmd, "json");
	if (json_filter && json_is_array(json_filter)) {
		json_error_t error;
		json_t *js = json_loads(text.c_str(), JSON_REJECT_DUPLICATES, &error);
		json_t *newjs = json_object();
		json_t *value;

		json_array_foreach(json_filter, value) {
			json_t *p_js = js;
			std::string key;
			std::vector<std::string> vlist;
			std::string v = json_string_value(value);

			split(v, ".", &vlist);
			foreach(vlist, i) {
				key = *i;
				p_js = json_geto(p_js, key.c_str());
				if (p_js == NULL)
					break;
			}
			if (p_js)
				json_seto(newjs, key.c_str(), p_js);
		}
		text = json_dumps(newjs, 2);
		json_delete(newjs);
		json_delete(js);
	}

	int in_size = text.size();
	int out_size = BASE64_SIZE(in_size) + 1;

	char *out_buffer = (char *)calloc(1, out_size);
	base64encode((unsigned char *)text.c_str(), in_size, (unsigned char*)out_buffer, out_size);
	json_sets(cmd, "data", out_buffer);
	char *body = json_dumps(cmd, 2);

	UrlPost("", body, text, dest);

	delete body;
	delete out_buffer;

	return 0;
}

bool KolaClient::Login(void)
{
	json_error_t error;
	std::string text;

	if (UrlGet("/login?user_id=000001", text) == false)
		return false;

	json_t *js = json_loads(text.c_str(), JSON_REJECT_DUPLICATES, &error);

	if (js) {
		LOCK(lock);
		loginKey = json_gets(js, "key", "");
		loginKeyCookie = "key=" + loginKey;
		UNLOCK(lock);

		std::cout << loginKey << std::endl;
		baseUrl = json_gets(js, "server", baseUrl.c_str());
		json_t *cmd = json_geto(js, "command");
		const char *dest = json_gets(js, "dest", NULL);
		if (cmd && dest && json_is_array(cmd)) {
			json_t *value;
			json_array_foreach(cmd, value)
				ProcessCommand(value, dest);
		}

		nextLoginSec = json_geti(js, "next", nextLoginSec);
		json_delete(js);
	}

	return 0;
}

bool KolaClient::UpdateMenu(void)
{
	json_error_t error;
	json_t *js;
	std::string text;

	if ( UrlGet("/video/getmenu", text) == false)
		return false;

	if (text.size() == 0) {
		return false;
	}

//	std::cout << text << std::endl;
	menuMap.clear();
	js = json_loads(text.c_str(), JSON_REJECT_DUPLICATES, &error);

	if (js) {
		json_t *value;
		json_array_foreach(js, value) {
			const char *name = json_gets(value, "name", "");
			menuMap.insert(std::pair<std::string, KolaMenu>(name, KolaMenu(value)));
		}
		json_delete(js);
	}

	return true;
}

KolaMenu KolaClient::operator[] (const char *name)
{
	return GetMenuByName(name);
}

KolaMenu KolaClient::operator[] (int index)
{
	std::map<std::string, KolaMenu>::iterator it = menuMap.begin();
	for(; it != menuMap.end() && index; it++, index--);

	if (index == 0 && it != menuMap.end())
		return it->second;
	else
		throw std::out_of_range("index");
}

KolaMenu KolaClient::GetMenuByCid(int cid)
{
	foreach(menuMap, i) {
		if (i->second.cid == cid)
			return i->second;
	}
	// TODO
	return KolaMenu();
}

KolaMenu KolaClient::GetMenuByName(const char *menuName)
{
	KolaMenu ret;
	std::map<std::string, KolaMenu>::iterator it;

	if (menuName == NULL)
		throw std::invalid_argument(menuName);

	it = menuMap.find(menuName);

	if (it != menuMap.end())
		return it->second;

	UpdateMenu();
	it = menuMap.find(menuName);

	if (it != menuMap.end())
		ret = it->second;

	return ret;
}

static void cancel(void *any)
{
	printf("Login thread canceled!!\n");
}

void *kola_login_thread(void *arg)
{
	KolaClient *client = (KolaClient*)arg;

	pthread_cleanup_push(cancel, NULL);
	while (client->running) {
		sleep(client->nextLoginSec);
		pthread_testcancel();
		client->Login();
		pthread_testcancel();
	}
	pthread_cleanup_pop(0);

	pthread_exit(NULL);

	return NULL;
}

