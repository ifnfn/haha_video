#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sstream>
#include <zlib.h>
#include <openssl/md5.h>
#include <signal.h>
#include <netdb.h>

#include "json.hpp"
#include "base64.hpp"
#include "kola.hpp"
#include "pcre.hpp"
#include "threadpool.hpp"
#include "script.hpp"

#include "http.hpp"
#include "resource.hpp"
#include "common.hpp"

#if TEST
//#	define SERVER_HOST "192.168.56.1"
#	define SERVER_HOST "127.0.0.1"
#	define PORT 9991
#else
#	define SERVER_HOST "www.kolatv.com"
#	define PORT 80
#endif

static string Serial("000002");
static size_t CacheSize = 1024 * 1024 * 1;
static int    ThreadNum = 10;

string GetSerial(void)
{
	return Serial;
}

/* Compress gzip data */
static int gzcompress(Bytef *data, uLong ndata, Bytef *zdata, uLong *nzdata)
{
	z_stream c_stream;
	int err = 0;
	int ret = -1;

	if(data && ndata > 0) {
		c_stream.zalloc = Z_NULL;
		c_stream.zfree = Z_NULL;
		c_stream.opaque = Z_NULL;
		if(deflateInit2(&c_stream, Z_DEFAULT_COMPRESSION, Z_DEFLATED,
					-MAX_WBITS, 8, Z_DEFAULT_STRATEGY) != Z_OK) return -1;
		c_stream.next_in    = data;
		c_stream.avail_in   = (uInt)ndata;
		c_stream.next_out   = zdata;
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

KolaClient::KolaClient(void)
{
	signal(SIGPIPE, SIG_IGN);

	nextLoginSec = 1;
	debug        = 0;
	authorized   = false;

	Curl::Instance();

	resManager = new ResourceManager(ThreadNum, CacheSize);
	threadPool = new ThreadPool(1);

	weather.SetPool(threadPool);
	LoginOne();
	thread = new Thread(this, &KolaClient::Login);
	thread->start();
}

bool KolaClient::InternetReady()
{
	return gethostbyname(SERVER_HOST) != NULL;
}

string KolaClient::GetServer()
{
	string ret;

	mutex.lock();
	if (BaseUrl.empty()) {
		char buffer[512];
		string ip = GetIP(SERVER_HOST);

		if (not ip.empty()) {
			sprintf(buffer, "http://%s:%d", ip.c_str(), PORT);
			BaseUrl = buffer;
		}
	}

	ret = BaseUrl;
	mutex.unlock();

	return ret;
}

void KolaClient::Quit(void)
{
	delete thread;

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
	url = GetFullUrl(url);

	Http http;
	http.Open(url.c_str(), GetCookie().c_str());
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

	if (url.compare(0, strlen("http://"), "http://") != 0)
		url = GetFullUrl(url);

	string new_body = gzip_base64(body, strlen(body));
	new_body = UrlEncode(new_body);

	Http http;
	http.Open(NULL, GetCookie().c_str());

	if (http.Post(url.c_str(), new_body.c_str()) != NULL) {
		ret = http.buffer.mem;

		return true;
	}

	return false;
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

bool KolaClient::Verify(const char *serial)
{
	if (serial) {
		Serial = serial;
		authorized = false;
		return LoginOne();
	}

	return authorized;
}

bool KolaClient::LoginOne()
{
	json_error_t error;
	string text;
	string url("/login");
	string params = "{";

	if (authorized) {
		params += stringlink("area"  , GetArea()) + ",";
		params += stringlink("cmd"   , authorized ? "1" : "0")+ ",";
	}
	params += stringlink("chipid", GetChipKey()) + ",";
	params += stringlink("serial", GetSerial());

	params += "}";

	if (UrlPost(url, params.c_str(), text) == false) {
		authorized = false;
		return false;
	}

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		string loginKey = json_gets(js, "key", "");
		SetCookie("key=" + loginKey);

		const char *p = json_gets(js, "server", NULL);
		if (p)
			this->SetServer(p);

		if (authorized) {
			json_t *cmd = json_geto(js, "command");
			if (cmd) {
				const char *dest = json_gets(js, "dest", NULL);
				if (dest && json_is_array(cmd)) {
					json_t *value;
					json_array_foreach(cmd, value)
						ProcessCommand(value, dest);
				}
			}

			ScriptCommand script;
			if (json_get_variant(js, "script", &script))
				script.Run();
		}

		nextLoginSec = (int)json_geti(js, "next", nextLoginSec);
		json_delete(js);

		authorized = true;
	}

	return true;
}

void KolaClient::ClearMenu()
{
	map<string, IMenu*>::iterator it;
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
			KolaMenu* menu = new KolaMenu();
			menu->Parser(value);
			menuMap.insert(pair<string, IMenu*>(name, menu));
		}
		json_delete(js);
		return true;
	}

	return false;
}

IMenu* KolaClient::operator[] (const char *name)
{
	return GetMenuByName(name);
}

IMenu* KolaClient::operator[] (int index)
{
	map<string, IMenu*>::iterator it = menuMap.begin();
	for(; it != menuMap.end() && index; it++, index--);

	if (index == 0 && it != menuMap.end())
		return it->second;

	return NULL;
}

IMenu* KolaClient::GetMenuByCid(int cid)
{
	foreach(menuMap, i) {
		if (i->second->cid == cid)
			return i->second;
	}

	return NULL;
}

IMenu* KolaClient::GetMenuByName(const char *menuName)
{
	map<string, IMenu*>::iterator it;

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

bool KolaClient::GetInfo(KolaInfo &info) {
	if (Info.Empty()) {
		json_t *js = json_loadurl("/video/getinfo");

		if (js) {
			json_get_stringlist(js, "source", &Info.VideoSource);
			json_get_stringlist(js, "resolution", &Info.Resolution);

			json_delete(js);
		}
	}

	info = Info;

	return not Info.Empty();
}

static void cancel(void *any)
{
	printf("Login thread canceled!!\n");
}

void KolaClient::Login()
{
	pthread_cleanup_push(cancel, NULL);
	while (thread->_state) {
		pthread_testcancel();
		LoginOne();
		pthread_testcancel();
		sleep(nextLoginSec);
	}
	pthread_cleanup_pop(0);

	pthread_exit(NULL);
}

KolaClient& KolaClient::Instance(const char *serial, size_t cache_size, int thread_num)
{
	if (serial)
		Serial = serial;

	if (cache_size)
		CacheSize = cache_size;

	if (thread_num)
		ThreadNum = thread_num;

	static KolaClient m_kola;

	return m_kola;
}

void KolaClient::SetPicutureCacheSize(size_t size)
{
	this->resManager->SetCacheSize(size);
}

string KolaClient::GetArea()
{
	static string local_area;

	if (local_area.empty()) {
		LuaScript &lua = LuaScript::Instance();
		vector<string> args;
		args.push_back("");

		local_area = lua.RunScript(args, "getip", "getip");
	}

	return local_area;
}

bool KolaClient::GetArea(KolaArea &area)
{
	static KolaArea local_area;

	if (local_area.Empty()) {
		json_error_t error;
		LuaScript &lua = LuaScript::Instance();
		vector<string> args;
		args.push_back("");

		string text = lua.RunScript(args, "getip", "getip_detail");

		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

		if (js) {
			local_area.ip       = json_gets(js, "ip", "");
			local_area.isp      = json_gets(js, "isp", "");
			local_area.country  = json_gets(js, "country", "");
			local_area.city     = json_gets(js, "city", "");
			local_area.province = json_gets(js, "province", "");
			json_delete(js);
		}
	}

	if (not local_area.Empty()) {
		area = local_area;

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
	if (url.compare(0, strlen("http://"), "http://") != 0)
		return UrlLink(GetServer(), url);
	else
		return url;
}

void KolaClient::CleanResource()
{
	resManager->Clear();
}

void KolaClient::SetServer(string server)
{
	mutex.lock();
	BaseUrl = server;
	mutex.unlock();
}

void KolaClient::SetCookie(string cookie)
{
	mutex.lock();
	this->Cookie = cookie;
	mutex.unlock();
}

string KolaClient::GetCookie()
{
	string ret;

	mutex.lock();
	ret = this->Cookie;
	mutex.unlock();

	return ret;
}

IObject::IObject()
{
	client = &KolaClient::Instance();
}


