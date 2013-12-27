#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"

KolaVideo::KolaVideo(json_t *js)
{
	urls = NULL;
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
	if (urls)
		delete urls;
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
	json_gets(js   , "playUrl"      , playUrl);
	json_gets(js   , "directPlayUrl", directPlayUrl);
	width          = (int)json_geti(js, "width", 0);
	height         = (int)json_geti(js, "height", 0);
	totalBytes     = (int)json_geti(js, "totalBytes", 0);
	fps            = (int)json_geti(js, "fps", 0);

	//	json_get_stringlist(js, "resolution", &resolution);
	json_get_variant(js, "info", &sc_info);
	json_get_variant(js, "resolution", &sc_resolution);
	//cout << resolution.ToString() << endl;

	return true;
}

void KolaVideo::GetResolution(StringList& res)
{
	if (urls == NULL) {
		string text = sc_resolution.GetString();
		urls = new VideoUrls(text);
	}

	if (urls)
		urls->GetResolution(res);
}

string KolaVideo::GetVideoUrl(string res)
{
	if (urls == NULL) {
		string text = sc_resolution.GetString();

		if (not text.empty())
			urls = new VideoUrls(text);
	}
	if (urls)
		return urls->Get(res);

	return "";

#if 0
	string ret;
	string url = "/video/geturl?vid=" + vid;

	if (not res.empty())
		url = url + "&resolution=" + res;

	json_t *js = json_loadurl(url.c_str());

	if (js == NULL)
		return "";

	if (json_is_array(js)) {
		json_t *v;
		json_array_foreach(js, v) {
			if (res == json_gets(v, "name", "") || res.empty()) {
				if (json_gets(v, "url", ret) == true)
					break;
			}
		}
	}

	json_delete(js);

	return ret;
#endif
}

string KolaVideo::GetInfo()
{
	return sc_info.GetString();
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

VideoUrls::VideoUrls(string text)
{
	json_error_t error;
	const char *key;
	json_t *value;

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	json_object_foreach(js, key, value) {
		Variant *var = new Variant(value);
		if (json_geti(value, "default", 0) == 1) {
			defaultKey = key;
		}
		urls.insert(pair<string, Variant*>(key, var));
	}

	json_delete(js);
}

VideoUrls::~VideoUrls()
{
	for (map<string, Variant*>::iterator it = urls.begin(); it != urls.end(); it++) {
		delete it->second;
	}
}

void VideoUrls::GetResolution(StringList& res)
{
	for (map<string, Variant*>::iterator it = urls.begin(); it != urls.end(); it++) {
		res.Add(it->first);
	}
}

Variant *VideoUrls::GetVariant(string &key)
{
	Variant *ret = NULL;
	if (key.empty())
		key = defaultKey;
	map<string ,Variant*>::iterator it = urls.find(key);
	if (it != urls.end())
		ret = it->second;

	return ret;
}

string VideoUrls::Get(string &key)
{
	Variant *var = GetVariant(key);

	if (var)
		return var->GetString();

	return "";
}
