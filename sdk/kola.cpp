#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <pcre.h>
#include <iostream>
#include <fstream>
#include <ios>
#include <sstream>
#include <stdexcept>
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <zlib.h>
#include <openssl/md5.h>

#include "json.h"
#include "httplib.h"
#include "base64.hpp"
#include "kola.hpp"
#include "pcre.hpp"
#include "threadpool.hpp"

#if 1
#define SERVER_HOST "127.0.0.1"
#define PORT 9991
#else
#define SERVER_HOST "121.199.20.175"
//#define SERVER_HOST "112.124.60.152"
//#define SERVER_HOST "www.kolatv.com"

#define PORT 80
#endif

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

static std::string chipKey(void)
{
	return "000001";
}

static std::string MD5STR(const char *data)
{
	MD5_CTX ctx;
	unsigned char md[16];
	char buf[33]={'\0'};

	MD5_Init(&ctx);
	MD5_Update(&ctx, data,strlen(data));
	MD5_Final(md,&ctx);

	for(int i=0; i<16; i++ ){
		sprintf(buf+ i * 2,"%02X", md[i]);
	}

	return std::string(buf);
}

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
	Byte *zdata = (Byte*)malloc(ndata * 2 + 4);
	uLong nzdata = ndata * 2;

	if (gzcompress((Bytef *)data, (uLong)ndata, zdata + 2, &nzdata) == 0) {
		zdata[0] = 0x5A;
		zdata[1] = 0xA5;
		data = (const char*)zdata;
		ndata = nzdata + 2;
	}
	int out_size = BASE64_SIZE(ndata) + 1;

	char *out_buffer = (char *)calloc(1, out_size);
	base64encode((unsigned char *)data, ndata, (unsigned char*)out_buffer, out_size);

	ret = out_buffer;

	free(out_buffer);
	free(zdata);

	return ret;
}

Picture::Picture(std::string fileName) {
	data = NULL;
	size = 0;
	inCache = false;
	used = false;
	this->fileName = fileName;
}

Picture::Picture() {
	data = NULL;
	size = 0;
	inCache = false;
	fileName = "";
}

Picture::~Picture() {
}

bool Picture::Destroy() {
	if (data) {
		free(data);
		data = NULL;
	}
	size = 0;

	return true;
}

bool Picture::Run()
{
	if (inCache == true)
		return inCache;
	KolaClient *client = &KolaClient::Instance();

	bool ok = false;
	http_resp_t *http_resp = NULL;

	if (client->UrlGet("", fileName.c_str(), (void**)&http_resp)) {
		size = http_resp->body_len;
		data = malloc(size);
		memcpy(data, http_resp->body, size);
		inCache = true;
		ok = true;
	}
	http_resp_free(http_resp);

	return ok;
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
	json_t *sort = json_geto(js, "sort");

	client = &KolaClient::Instance();

	if (filter) {
		const char *key;
		json_t *values;
		json_object_foreach(filter, key, values) {
			json_t *v;
			std::string list;
			json_array_foreach(values, v)
				list = list + json_string_value(v) + ",";
			this->Filter.filterKey.insert(std::pair<std::string, FilterValue>(key, FilterValue(list)));
		}
	}

	if (sort) {
		json_t *v;
		std::string list;
		json_array_foreach(sort, v)
			list = list + json_string_value(v) + ",";
		this->Sort.Split(list);
	}
}

KolaMenu::KolaMenu(const KolaMenu &m) {
	name     = m.name;
	cid      = m.cid;
	PageSize = m.PageSize;
	PageId   = m.PageId;
	client   = m.client;
	Filter   = m.Filter;
	Sort     = m.Sort;
//	client = &KolaClient::Instance();
}

int KolaMenu::GetPage(AlbumPage &page, int pageNo)
{
	char url[256];
	int count = 0;
	std::string text;
	std::string body("{");
	std::string filter = Filter.GetJsonStr();
	std::string sort = Sort.GetJsonStr();

	page.Clear();
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
	if (pageNo == -1)
		PageId++;
	else
		PageId = pageNo;

	sprintf(url, "/video/list?page=%d&size=%d&menu=%s", PageId, PageSize, name.c_str());
	if (client->UrlPost(url, body.c_str(), text) == true) {
		json_error_t error;
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		if (js) {
			json_t *results = json_geto(js, "result");

			if (results && json_is_array(results)) {
				json_t *value;
				json_array_foreach(results, value)
					page.PutAlbum(new KolaAlbum(value));
			}

//			std::cout << text << std::endl;
			json_decref(js);
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
		free(p);
	}

	nextLoginSec = 3;
	running = true;
	havecmd = true;

	threadPool = (void*)pool_create(MAX_THREAD_POOL_SIZE);

	pthread_mutex_init(&lock, NULL);
	Login(true);
	pthread_create(&thread, NULL, kola_login_thread, this);
}

void KolaClient::Quit(void)
{
	running = false;
	pthread_cancel(thread);
	pthread_join(thread, NULL);
	printf("KolaClient Quit: %p\n", this);
}

KolaClient::~KolaClient(void)
{
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
		*resp = NULL;
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

bool KolaClient::UrlGetCache(std::string url, std::string &ret, const char *home_url)
{
	bool rc = false;
	std::string key = MD5STR(home_url);
	char filename[128];
	sprintf(filename, "../cache/%s", key.c_str());

	std::ifstream in(filename);

	if (in.is_open()) {
		printf("Find cache : %s\n", filename);
		std::istreambuf_iterator<char> beg(in), end;
		ret = std::string(beg, end);

		in.close();
		return true;
	}
	else {
		printf("download ... %s", home_url);
		fflush(stdout);

		rc = UrlGet(url, ret, home_url);
		if (rc) {
			printf("OK\n");
			std::ofstream out(filename);
			out << ret;
			out.close();
		}
		else
			printf("fail\n");

		return rc;
	}
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

	if (body)
		new_body = gzip_base64(body, strlen(body));
	rc = http_post(http_client, url.c_str(), &http_resp, new_body.c_str(), cookie.c_str());
	if (rc) {
		if (http_resp && http_resp->body)
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
	printf("[%s]: %s\n", name, source);

	if (UrlGetCache("", text, source) == false)
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
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
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
		json_decref(newjs);
		json_decref(js);
	}

	json_sets(cmd, "data", text.c_str());
	char *body = json_dumps(cmd, 2);

	UrlPost("", body, text, dest);

	free(body);

	return 0;
}

bool KolaClient::Login(bool quick)
{
	json_error_t error;
	std::string text;
	std::string url("/login?user_id=");

	url = url + chipKey();
	if (quick == true)
		url = url + "&cmd=0";
	else
		url = url + "&cmd=1";

	if (UrlGet(url, text) == false)
		return false;

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		LOCK(lock);
		loginKey = json_gets(js, "key", "");
		loginKeyCookie = "key=" + loginKey;
		UNLOCK(lock);

		baseUrl = json_gets(js, "server", baseUrl.c_str());
		json_t *cmd = json_geto(js, "command");
		if (cmd) {
			const char *dest = json_gets(js, "dest", NULL);
			if (dest && json_is_array(cmd)) {
				json_t *value;
				json_array_foreach(cmd, value)
					ProcessCommand(value, dest);
			}
		}
		else {
			havecmd = false;
			printf("No found command!\n");
		}

		nextLoginSec = json_geti(js, "next", nextLoginSec);
		json_decref(js);
	}

	return true;
}

void KolaClient::ClearMenu()
{
	std::map<std::string, KolaMenu*>::iterator it;
	for (it = menuMap.begin(); it != menuMap.end(); it++)
		delete it->second;

	menuMap.clear();
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
	ClearMenu();
	js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		json_t *value;
		json_array_foreach(js, value) {
			const char *name = json_gets(value, "name", "");
			menuMap.insert(std::pair<std::string, KolaMenu*>(name, new KolaMenu(value)));
		}
		json_decref(js);
	}

	return true;
}

KolaMenu* KolaClient::operator[] (const char *name)
{
	return GetMenuByName(name);
}

KolaMenu* KolaClient::operator[] (int index)
{
	std::map<std::string, KolaMenu*>::iterator it = menuMap.begin();
	for(; it != menuMap.end() && index; it++, index--);

	if (index == 0 && it != menuMap.end())
		return it->second;

	return NULL;
}

KolaMenu* KolaClient::GetMenuByCid(int cid)
{
	foreach(menuMap, i) {
		if (i->second->cid == cid)
			return i->second;
	}

	return NULL;
}

KolaMenu* KolaClient::GetMenuByName(const char *menuName)
{
	std::map<std::string, KolaMenu*>::iterator it;

	if (menuName == NULL)
		return NULL;

	it = menuMap.find(menuName);

	if (it != menuMap.end())
		return it->second;

	UpdateMenu();
	it = menuMap.find(menuName);

	if (it != menuMap.end())
		return it->second;

	return NULL;
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
		pthread_testcancel();
		client->Login(false);
		pthread_testcancel();
		sleep(client->nextLoginSec);
	}
	pthread_cleanup_pop(0);

	pthread_exit(NULL);

	return NULL;
}

KolaClient& KolaClient::Instance(void)
{
	static KolaClient m_kola;

	return m_kola;
}
