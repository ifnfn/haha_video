#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "script.hpp"

KolaVideo::KolaVideo(json_t *js)
{
	width = height = fps = totalBytes = totalBlocks = 0;
	totalDuration = 0.0;
	order = 0;
	isHigh = 0;
	videoPlayCount = 0;
	videoScore = 0.0;
	playLength = 0.0;
	info_js = new ScriptCommand();

	if (js)
		LoadFromJson(js);
}

KolaVideo::~KolaVideo()
{
	delete info_js;
}

bool KolaVideo::LoadFromJson(json_t *js)
{
	json_t *sub;

	json_gets(js   , "name"           , name);
	json_gets(js   , "playlistid"     , playlistid);
	json_gets(js   , "pid"            , pid);
	json_gets(js   , "vid"            , vid);
	cid            = json_geti(js   , "cid"            , 0);
	order          = json_geti(js   , "order"          , 0);
	isHigh         = json_geti(js   , "isHigh"         , 0);

	videoPlayCount = json_geti(js   , "videoPlayCount" , 0);
	videoScore     = json_getreal(js, "videoScore"     , 0.0);
	playLength     = json_getreal(js, "playLength"     , 0.0);

	json_gets(js   , "showName"       , showName);
	json_gets(js   , "publishTime"    , publishTime);
	json_gets(js   , "videoDesc"      , videoDesc);

	json_gets(js   , "smallPicUrl"    , smallPicUrl);
	json_gets(js   , "largePicUrl"    , largePicUrl);
	json_gets(js   , "playUrl"        , playUrl);
	json_gets(js   , "directPlayUrl"  , directPlayUrl);
	totalDuration  = json_getreal(js, "totalDuration", 0.0);
	width          = json_geti(js   , "width", 0);
	height         = json_geti(js   , "height", 0);
	totalBlocks    = json_geti(js   , "totalBlocks", 0);
	totalBytes     = json_geti(js   , "totalBytes", 0);
	fps            = json_geti(js   , "fps", 0);

	json_get_stringlist(js, "resolution", &resolution);
	json_get_script(js, "info", info_js);
	//std::cout << resolution.ToString() << std::endl;

	return true;
}

std::string KolaVideo::GetVideoUrl(std::string res)
{
	std::string ret;
	std::string url = "/video/geturl?vid=" + vid;

	if (res != "")
		url = url + "&resolution=" + res;

	json_t *js = json_loadurl(url.c_str());

	if (js == NULL)
		return "";

	if (json_is_array(js)) {
		json_t *v;
		json_array_foreach(js, v) {
			if (res == json_gets(v, "name", "") || res == "") {
				if (json_gets(v, "url", ret) == true)
					break;
			}
		}
	}

	json_delete(js);

	return ret;
}

std::string KolaVideo::GetInfo()
{
	if (info_js) {
		return info_js->Run();
	}
}



bool KolaEpg::LoadFromText(std::string text)
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
	time_t t = time(NULL);

	return Get(e, t);
}

bool KolaEpg::GetNext(EPG &e)
{
	bool found = false;
	time_t t = time(NULL);

	for (std::vector<EPG>::iterator it = begin(); it != end(); it++) {
		if (t >= it->startTime && (it->startTime + it->duration < t)) {
			found = true;
			continue;
		}
		if (found) {
			e = *it;
			break;
		}
	}

	return found;
}

bool KolaEpg::Get(EPG &e, time_t t)
{
	for (std::vector<EPG>::iterator it = begin(); it != end(); it++) {
		if (t >= it->startTime && (it->startTime + it->duration < t)) {
			e = *it;
			return true;
		}
	}

	return false;
}

