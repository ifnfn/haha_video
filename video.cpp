#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"
#include "kolabase.hpp"

KolaVideo::KolaVideo() {
	width = height = fps = totalBytes = 0;
	order = 0;
	isHigh = 0;
	videoPlayCount = 0;
	videoScore = 0.0;
	playLength = 0.0;
}

KolaVideo::~KolaVideo() {
}

KolaEpg *KolaVideo::NewEPG()
{
	if (not EpgInfo.Empty()) {
		KolaEpg *epg = new KolaEpg(EpgInfo);
		epg->SetPool(client->threadPool);

		return epg;
	}

	return NULL;
}

void KolaVideo::Parser(json_t *js)
{
	json_gets(js   , "name"         , name);
	json_gets(js   , "pid"          , pid);
	json_gets(js   , "vid"          , vid);
	cid            = (int)json_geti(js   , "cid"       , 0);
	order          = (int)json_geti(js   , "order"     , 0);
	isHigh         = (int)json_geti(js   , "isHigh"    , 0);

	videoPlayCount = json_geti(js   , "videoPlayCount" , 0);
	videoScore     = json_getreal(js, "videoScore"     , 0.0);
	playLength     = json_getreal(js, "playLength"     , 0.0);

	json_gets(js   , "showName"     , showName);
	json_gets(js   , "publishTime"  , publishTime);
	json_gets(js   , "videoDesc"    , videoDesc);

	json_gets(js   , "smallPicUrl"  , smallPicUrl);
	json_gets(js   , "largePicUrl"  , largePicUrl);
	json_gets(js   , "directPlayUrl", directPlayUrl);
	width          = (int)json_geti(js, "width"     , 0);
	height         = (int)json_geti(js, "height"    , 0);
	totalBytes     = (int)json_geti(js, "totalBytes", 0);
	fps            = (int)json_geti(js, "fps"       , 0);

	json_get_variant(js, "info", &EpgInfo);
	json_get_variant(js, "resolution", &Resolution);
	Resolution.vid = vid;
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

UrlCache::UrlCache()
{
	timeout = 20;
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
