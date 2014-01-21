#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"


KolaVideo::KolaVideo()
{
}

KolaVideo::~KolaVideo()
{
}

void KolaVideo::Parser(json_t *js)
{
	json_gets(js   , "name"         , name);
	json_gets(js   , "pid"          , pid);
	json_gets(js   , "vid"          , vid);
	cid            = (int)json_geti(js   , "cid"            , 0);
	order          = (int)json_geti(js   , "order"          , 0);
	isHigh         = (int)json_geti(js   , "isHigh"         , 0);

	videoPlayCount = json_geti(js   , "videoPlayCount" , 0);
	videoScore     = json_getreal(js, "videoScore"     , 0.0);
	playLength     = json_getreal(js, "playLength"     , 0.0);

	json_gets(js   , "showName"     , showName);
	json_gets(js   , "publishTime"  , publishTime);
	json_gets(js   , "videoDesc"    , videoDesc);

	json_gets(js   , "smallPicUrl"  , smallPicUrl);
	json_gets(js   , "largePicUrl"  , largePicUrl);
	json_gets(js   , "directPlayUrl", directPlayUrl);
	width          = (int)json_geti(js, "width", 0);
	height         = (int)json_geti(js, "height", 0);
	totalBytes     = (int)json_geti(js, "totalBytes", 0);
	fps            = (int)json_geti(js, "fps", 0);

	//	json_get_stringlist(js, "resolution", &resolution);
	json_get_variant(js, "info", &sc_info);
	json_get_variant(js, "resolution", &Resolution);
	Resolution.vid = vid;
	//cout << resolution.ToString() << endl;
}

void KolaVideo::GetResolution(StringList& res)
{
	Resolution.GetResolution(res);
}

void KolaVideo::SetResolution(string &res)
{
	Resolution.SetResolution(res);
}

string KolaVideo::GetVideoUrl()
{
	return Resolution.GetVideoUrl();
}

bool KolaVideo::GetEPG(KolaEpg &epg)
{
	string text = sc_info.GetString();

	if (not text.empty()) {
		epg.LoadFromText(text);
		return true;
	}

	return false;
}

bool KolaEpg::LoadFromText(string text)
{
	bool ret = false;

	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);

	if (js)
		ret = LoadFromJson(js);

	json_delete(js);

	return ret;
}

bool KolaEpg::LoadFromJson(json_t *js)
{
	json_t *v;
	json_array_foreach(js, v) {
		EPG e;
		e.startTime = json_geti(v, "time", 0);
		e.duration = json_geti(v, "duration", 0);
		json_gets(v, "title", e.title);
		json_gets(v, "time_string", e.timeString);

		push_back(e);
	}

	return true;
}

bool KolaEpg::GetCurrent(EPG &e)
{
	return Get(e, KolaClient::Instance().GetTime());
}

bool KolaEpg::GetNext(EPG &e)
{
	EPG ok;
	time_t t = KolaClient::Instance().GetTime();

	int count = (int)size();
	for (int i = count - 1; i >= 0; i--) {
		EPG x = at(i);

		if (t >= x.startTime) {
			e = ok;
			return true;
		}

		ok = x;
	}

	return false;
}

bool KolaEpg::Get(EPG &e, time_t t)
{
	int count = (int)size();

	for (int i = count - 1; i >= 0; i--) {
		EPG x = at(i);

		if (t >= x.startTime) {
			e = x;
			return true;
		}
	}

	return false;
}

UrlCache::UrlCache()
{
	timeout = 3600;
}

void UrlCache::SetTimeout(size_t sec)
{
	timeout = sec;
}

bool UrlCache::FindByVid(string &vid, string &url) {
	bool found = false;
	Update();

	mutex.lock();
	map<string, CacheUrl>::iterator it = mapList.find(vid);
	if (it != mapList.end()) {
		url = it->second.url;
		found = true;
	}
	mutex.unlock();

	return found;
}

void UrlCache::Set(string&vid, string &url)
{
	mutex.lock();
	mapList[vid] = url;
	mutex.unlock();
}

void UrlCache::Remove(string &vid)
{
	mutex.lock();
	mapList.erase(vid);
	mutex.unlock();
}

void UrlCache::Update()
{
	map<string, CacheUrl>::iterator it;

	time_t now;
	now = time(&now);

	mutex.lock();
	for(it = mapList.begin(); it != mapList.end();) {
		if (now - it->second.t > timeout)
			mapList.erase(it++);
		else
			it++;

	}
	mutex.unlock();
}

