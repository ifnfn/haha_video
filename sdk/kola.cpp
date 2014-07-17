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
//#	define SERVER_HOST "www.kolatv.com"
#	define SERVER_HOST "114.215.174.227"
#	define PORT 80
#endif

static string Serial;
static size_t CacheSize = 1024 * 512;
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

bool KolaClient::KolaReady()
{
	string ret;
	if (this->UrlGet("/static/info", ret)) {

		return ret.compare(0, 2, "OK") == 0;
	}

	return false;
}

bool KolaClient::InternetReady()
{
	string ip = GetIP(SERVER_HOST);

	return not ip.empty();
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
	Http http;

	url = GetFullUrl(url);
	http.Open(url.c_str());
	if (http.Get() != NULL) {
		ret.assign(http.Data().mem);

		return true;
	}

	if (http.httpcode == 302)
		printf("[Kolatv] Error unauthorized, error cdoe: %d\n", http.httpcode);

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

	if (http.Post(url.c_str(), new_body.c_str()) != NULL) {
		ret = http.buffer.mem;

		return true;
	}

	return false;
}

bool KolaClient::Verify(const char *serial)
{
	if (serial) {
		Serial = serial;
		authorized = false;
		LoginOne();
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
		KolaArea area;
		if (GetArea(area))
			params += stringlink("area"  , area.toString(), "", ",");

		params += stringlink("cmd", authorized ? "1" : "0", "", ",");
	}
	params += stringlink("chipid",  GetChipKey(), "", ", ");
	params += stringlink("serial",  GetSerial() , "", ", ");
	params += stringlink("version", KOLA_VERSION, "", " }");

	if (UrlPost(url, params.c_str(), text) == false) {
		authorized = false;
		nextLoginSec = 1;

		return false;
	}

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js) {
		const char *p = json_gets(js, "server", NULL);
		if (p)
			SetServer(p);

		nextLoginSec = (int)json_geti(js, "next", nextLoginSec);

		string loginKey = json_gets(js, "key", "");

		authorized = not loginKey.empty();

		if (authorized) {
			ScriptCommand script;
			if (json_get_variant(js, "script", &script))
				script.Run();
		}

		json_delete(js);
	}

	return true;
}

void KolaClient::ClearMenu()
{
	for(map<string, KolaMenu*>::iterator it = menuMap.begin(); it != menuMap.end(); it++)
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
			KolaMenu *menu = new KolaMenu();
			menu->Parser(value);
			menuMap.insert(pair<string, KolaMenu*>(name, menu));
		}
		json_delete(js);
		return true;
	}

	return false;
}

KolaMenu* KolaClient::Index(int index)
{
	map<string, KolaMenu*>::iterator it = menuMap.begin();
	for(; it != menuMap.end() && index; it++, index--);

	if (index == 0 && it != menuMap.end())
		return it->second;

	return NULL;
}

KolaMenu* KolaClient::GetMenu(int cid)
{
	foreach(menuMap, i) {
		if (i->second->cid == cid)
			return i->second;
	}

	return NULL;
}

KolaMenu* KolaClient::GetMenu(const char *menuName)
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

bool KolaClient::GetArea(KolaArea &area)
{
	static KolaArea local_area;

	if (local_area.Empty()) {
		json_error_t error;
		LuaScript &lua = LuaScript::Instance();
		vector<string> args;
		args.push_back("");

		string text = lua.RunScript("getip", "getip_detail", args);

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

		string ret = lua.RunScript("getip", "gettime", args);

		if (not ret.empty()) {
			init_time = atol(ret.c_str());
			hw_time = time(NULL);
		}
		else
			hw_time = 0;
	}

	size_t offset = time(NULL) - hw_time;
	time_t ret = init_time + offset;

	if (offset > 3600)
		init_time = 0;

	return ret;
}

string KolaClient::GetFullUrl(string url)
{
	string full_url;

	if (url.compare(0, strlen("http://"), "http://") != 0)
		full_url = UrlLink(GetServer(), url);
	else
		full_url = url;

#if 1
	if (full_url.find("?") == std::string::npos)
		full_url = full_url + "?";
	else
		full_url = full_url + "&";

	full_url = full_url + "chipid=" + GetChipKey() + "&serial=" + GetSerial();
	//printf("FullUrl: %s\n", full_url.c_str());
#endif

	return full_url;
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

IObject::IObject()
{
	client = &KolaClient::Instance();
}

bool KolaArea::Empty() {
	return ip.empty() && province.empty() && city.empty();
}

string KolaArea::toJson() {
	string ret = "\"area\" : {";

	ret += stringlink("country" , country , "", ",");
	ret += stringlink("province", province, "", ",");
	ret += stringlink("city"    , city    , "", "}");

	return ret;
}

string KolaArea::toString() {
	return country + "," + province + "," + city + "," + isp;
}
