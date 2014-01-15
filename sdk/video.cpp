#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"

KolaPlayer::KolaPlayer()
{
	_condvar = new ConditionVar();
	thread = new Thread(this, &KolaPlayer::Run);
	thread->start();
}

KolaPlayer::~KolaPlayer()
{
	thread->cancel();
	_condvar->broadcast();
	thread->join();
	delete _condvar;
}

void KolaPlayer::Run()
{
	while (thread->_state == true) {
		_condvar->lock();
		if (videoList.empty()) {
			_condvar->wait();
			_condvar->unlock();
		}
		else {
			VideoResolution &video = this->videoList.front();
			videoList.pop_front();
			_condvar->unlock();

			string url = video.GetVideoUrl();
			if (not url.empty())
				Play(video.defaultKey, url);
		}
	}
}

void KolaPlayer::AddVideo(IVideo *video)
{
	if (video) {
		_condvar->lock();
		videoList.clear();
		videoList.push_back(video->Resolution);
		_condvar->signal();
		_condvar->unlock();
	}
}

KolaVideo::KolaVideo(json_t *js)
{
	width = height = fps = totalBytes = 0;
	order = 0;
	isHigh = 0;
	videoPlayCount = 0;
	videoScore = 0.0;
	playLength = 0.0;

	if (js)
		LoadFromJson(js);
}

KolaVideo::~KolaVideo()
{
}

bool KolaVideo::LoadFromJson(json_t *js)
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
	//cout << resolution.ToString() << endl;

	return true;
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

bool VideoResolution::Empty()
{
	return urls.empty();
}

void VideoResolution::Clear()
{
	urls.clear();
}

void VideoResolution::Set()
{
	json_error_t error;
	const char *key;
	json_t *value;
	string text = GetString();

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	json_object_foreach(js, key, value) {
		if (json_geti(value, "default", 0) == 1) {
			defaultKey = key;
		}
		urls.insert(pair<string, Variant>(key, Variant(value)));
	}

	json_delete(js);
}

void VideoResolution::GetResolution(StringList& res)
{
	if (Empty())
		Set();
	for (map<string, Variant>::iterator it = urls.begin(); it != urls.end(); it++) {
		res.Add(it->first);
	}
}

void VideoResolution::SetResolution(string &res)
{
	this->defaultKey = res;
}

bool VideoResolution::GetVariant(string &key, Variant &var)
{
	if (key.empty())
		key = defaultKey;
	map<string ,Variant>::iterator it = urls.find(key);
	if (it != urls.end()) {
		var = it->second;
		return true;
	}

	return false;
}

string VideoResolution::GetVideoUrl()
{
	Variant var;

	if (Empty())
		Set();

	map<string ,Variant>::iterator it = urls.find(defaultKey);
	if (it != urls.end()) {
		var = it->second;
		return var.GetString();
	}

	return "";
}
