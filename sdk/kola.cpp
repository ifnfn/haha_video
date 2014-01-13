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
#include <signal.h>

#include "json.hpp"
#include "base64.hpp"
#include "kola.hpp"
#include "pcre.hpp"
#include "threadpool.hpp"
#include "script.hpp"

#include "http.hpp"
#include "resource.hpp"

#if TEST
#define SERVER_HOST "192.168.56.1"
//#define SERVER_HOST "127.0.0.1"
#define PORT 9991
#else
//#define SERVER_HOST "121.199.20.175"
//#define SERVER_HOST "112.124.60.152"
#define SERVER_HOST "www.kolatv.com"

#define PORT 80
#endif

#define MAX_THREAD_POOL_SIZE 8
#define TRY_TIMES 3

static string loginKey;
static string loginKeyCookie;
static string xsrf_cookie;

#if 1
#define LOCK(lock)   pthread_mutex_lock(&lock)
#define UNLOCK(lock) pthread_mutex_unlock(&lock)
#else
#define LOCK(lock)   do {} while(0)
#define UNLOCK(lock) do {} while(0)
#endif

static string chipKey(void)
{
	return "000001";
}

#if 1
string MD5STR(const char *data)
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

	return string(buf);
}
#endif

static char *GetIP(const char *hostp)
{
	char str[32];
	struct hostent *host = gethostbyname(hostp);

	if (host == NULL)
		return NULL;

	inet_ntop(host->h_addrtype, host->h_addr, str, sizeof(str));

	//	freehostent(host);
	return strdup(str);
}

static char *ReadStringFile(FILE *fp)
{
#define LEN 2048
	char *s = NULL;

	if (fp) {
		long size = 0;
		size_t len;
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
	int ret = -1;

	if(data && ndata > 0)
	{
		c_stream.zalloc = Z_NULL;
		c_stream.zfree = Z_NULL;
		c_stream.opaque = Z_NULL;
		if(deflateInit2(&c_stream, Z_DEFAULT_COMPRESSION, Z_DEFLATED,
					-MAX_WBITS, 8, Z_DEFAULT_STRATEGY) != Z_OK) return -1;
		c_stream.next_in  = data;
		c_stream.avail_in  = (uInt)ndata;
		c_stream.next_out = zdata;
		c_stream.avail_out  = (uInt)*nzdata;

		while (c_stream.avail_in != 0 && c_stream.total_out < *nzdata) {
			if (deflate(&c_stream, Z_NO_FLUSH) != Z_OK)
				goto out;
		}
		if(c_stream.avail_in != 0) {
			ret = c_stream.avail_in;
			goto out;
		}
		for (;;) {
			if((err = deflate(&c_stream, Z_FINISH)) == Z_STREAM_END) break;
			if(err != Z_OK)
				goto out;
		}
		if(deflateEnd(&c_stream) != Z_OK)
			return -1;
		*nzdata = c_stream.total_out;

		return 0;
	}

out:
	deflateEnd(&c_stream);
	return ret;
}

static string gzip_base64(const char *data, size_t ndata)
{
	string ret;
	Byte *zdata = (Byte*)malloc(ndata * 2 + 4);
	uLong nzdata = ndata * 2;

	if (gzcompress((Bytef *)data, (uLong)ndata, zdata + 2, &nzdata) == 0) {
		zdata[0] = 0x5A;
		zdata[1] = 0xA5;
		data = (const char*)zdata;
		ndata = nzdata + 2;
	}
	size_t out_size = BASE64_SIZE(ndata) + 1;

	char *out_buffer = (char *)calloc(1, out_size);
	base64encode((unsigned char *)data, ndata, (unsigned char*)out_buffer, out_size);

	ret = out_buffer;

	free(out_buffer);
	free(zdata);

	return ret;
}

void *kola_login_thread(void *arg);

KolaClient::KolaClient(void)
{
	signal(SIGPIPE, SIG_IGN);
	char buffer[512];

	char *ip = GetIP(SERVER_HOST);

	if (ip) {
		sprintf(buffer, "http://%s:%d", ip, PORT);
		baseUrl = buffer;
		free(ip);
	}

	nextLoginSec = 3;
	running = true;
	havecmd = true;
	debug = 0;

	threadPool = new ThreadPool(MAX_THREAD_POOL_SIZE);
	resManager = new ResourceManager(1024 * 1024 * 2);

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
	ClearMenu();
	Quit();
	delete threadPool;
	delete resManager;
}

bool KolaClient::UrlGet(string url, string &ret)
{
	const char *cookie = NULL;

	if (url.compare(0, strlen("http://"), "http://") != 0) {
		LOCK(lock);
		cookie = loginKeyCookie.c_str();
		url = GetFullUrl(url);
		UNLOCK(lock);
	}

	Http http;
	http.Set(url.c_str(), cookie);
	if (http.Get() != NULL) {
		ret.assign(http.Data().mem);

		return true;
	}

	return false;
}

bool KolaClient::UrlPost(string url, const char *body, string &ret)
{
	if (body == NULL)
		return false;

	const char *cookie = NULL;

	if (url.compare(0, strlen("http://"), "http://") != 0) {
		LOCK(lock);
		cookie = loginKeyCookie.c_str();
		url = GetFullUrl(url);
		UNLOCK(lock);
	}

	string new_body = gzip_base64(body, strlen(body));
	new_body = UrlEncode(new_body);

	Http http;
	http.Set(NULL, cookie);

	if (http.Post(url.c_str(), new_body.c_str()) != NULL) {
		ret = http.buffer.mem;

		return true;
	}

	return false;
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
	string text;
	KolaPcre pcre;
	const char *source = json_gets(cmd, "source", NULL);

	text = json_gets(cmd, "text", "");
	if (source) {
		if (UrlGet(source, text) == false)
			return false;
	}

	if (text.size() == 0)
		return false;

	json_t *regular = json_geto(cmd, "regular");
	if (regular && json_is_array(regular)) {
		json_t *value;

		json_array_foreach(regular, value) {
			const char *r = json_string_value(value);
			pcre.AddRule(r);
			text = pcre.MatchAll(text.c_str());
			pcre.ClearRules();
		}

		//text = pcre.MatchAll(text.c_str());
	}

	json_t *json_filter = json_geto(cmd, "json");
	if (json_filter && json_is_array(json_filter)) {
		json_error_t error;
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		json_t *newjs = json_object();
		json_t *value;

		json_array_foreach(json_filter, value) {
			json_t *p_js = js;
			string key;
			vector<string> vlist;
			string v = json_string_value(value);

			split(v, ".", vlist);
			foreach(vlist, i) {
				key = *i;
				p_js = json_geto(p_js, key.c_str());
				if (p_js == NULL)
					break;
			}
			if (p_js)
				json_seto(newjs, key.c_str(), p_js);
		}
		json_dump_str(newjs, text);
		json_delete(newjs);
		json_delete(js);
	}

	json_sets(cmd, "data", text.c_str());

	char *body = json_dumps(cmd, 2);
	UrlPost(dest, body, text);
	free(body);

	return 0;
}

bool KolaClient::Login(bool quick)
{
	json_error_t error;
	string text;
	string url("/login?user_id=");

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
		else
			havecmd = false;

		nextLoginSec = (int)json_geti(js, "next", nextLoginSec);
		json_delete(js);
	}

	return true;
}

void KolaClient::ClearMenu()
{
	map<string, KolaMenu*>::iterator it;
	for (it = menuMap.begin(); it != menuMap.end(); it++)
		delete it->second;

	menuMap.clear();
}

bool KolaClient::UpdateMenu(void)
{
	json_t *js;

	js = json_loadurl("/video/getmenu");

	if (js) {
		json_t *value;

		ClearMenu();
		json_array_foreach(js, value) {
			const char *name = json_gets(value, "name", "");
			menuMap.insert(pair<string, KolaMenu*>(name, new KolaMenu(value)));
		}
		json_delete(js);
		return true;
	}

	return false;
}

KolaMenu* KolaClient::operator[] (const char *name)
{
	return GetMenuByName(name);
}

KolaMenu* KolaClient::operator[] (int index)
{
	map<string, KolaMenu*>::iterator it = menuMap.begin();
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

KolaInfo& KolaClient::GetInfo() {
	if (info.update == false) {
		json_t *js = json_loadurl("/video/getinfo");

		if (js) {
			json_get_stringlist(js, "source", &info.VideoSource);
			json_get_stringlist(js, "resolution", &info.Resolution);

			info.update = true;
			json_delete(js);
		}
	}

	return info;
}

KolaMenu* KolaClient::GetMenuByName(const char *menuName)
{
	map<string, KolaMenu*>::iterator it;

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

KolaClient& KolaClient::Instance(const char *user_id)
{
	static KolaClient m_kola;

	return m_kola;
}

void KolaClient::SetPicutureCacheSize(size_t size)
{
	this->resManager->SetCacheSize(size);
}

string KolaClient::GetArea()
{
	LuaScript &lua = LuaScript::Instance();
	vector<string> args;
	args.push_back("");

	return lua.RunScript(args, "getip", "getip");
}

bool KolaClient::GetArea(KolaArea &area)
{
	json_error_t error;
	LuaScript &lua = LuaScript::Instance();
	vector<string> args;
	args.push_back("");

	string text = lua.RunScript(args, "getip", "getip_detail");

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		area.ip       = json_gets(js, "ip", "");
		area.isp      = json_gets(js, "isp", "");
		area.country  = json_gets(js, "country", "");
		area.city     = json_gets(js, "city", "");
		area.province = json_gets(js, "province", "");
		json_delete(js);

		return true;
	}

	return false;
}

time_t KolaClient::GetTime()
{
	static time_t init_time = 0;
	static time_t hw_time = 0;

	if (init_time == 0) {
		LuaScript &lua = LuaScript::Instance();
		vector<string> args;
		args.push_back("");

		string ret = lua.RunScript(args, "getip", "gettime");

		init_time = atol(ret.c_str());
		hw_time = time(NULL);
	}

	size_t offset = time(NULL) - hw_time;
	time_t ret = init_time + offset;

	if (offset > 3600)
		init_time = 0;

	return ret;
}

string KolaClient::GetFullUrl(string url)
{
	if (!url.empty() && url.at(0) != '/')
		return baseUrl + '/' + url;
	else
		return baseUrl + url;
	//url = uri_join(home_url, url.c_str());
	//url = uriJoin(home_url, url);
}
