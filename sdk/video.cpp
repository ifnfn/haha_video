#include <iostream>
#include <unistd.h>

#include "kola.hpp"
#include "json.h"
#include "base64.hpp"
#include "script.hpp"

VideoSegment::VideoSegment()
{
	duration = 0;
	size = 0;
}

VideoSegment::VideoSegment(json_t *js)
{
	LoadFromJson(js);
}

bool VideoSegment::LoadFromJson(json_t *js)
{
	url      = json_gets   (js, "url", "");
	newfile  = json_gets   (js, "new", "");
	size     = json_geti   (js, "size", 0);
	duration = json_getreal(js, "duration", 0.0);

	return true;
}

std::string VideoSegment::GetJsonStr(std::string *newUrl)
{
	char buffer[2048];
	if (newUrl == NULL)
		newUrl = &url;

	snprintf(buffer, 2047, "{\n\"url\":\"%s\",\n\"new\":\"%s\"\n,\"duration\":\"%.2f\"\n}",
			newUrl->c_str(), newfile.c_str(), duration);

	return std::string(buffer);
}

void VideoSegment::Run()
{
	std::string text;
	KolaClient *client =& KolaClient::Instance();

	if (client->UrlGet("", text, url.c_str()) == true)
		realUrl = GetJsonStr(&text);
	else
		realUrl = "";
}

KolaVideo::KolaVideo(json_t *js)
{
	width = height = fps = totalBytes = totalBlocks = 0;
	totalDuration = 0.0;
	order = 0;
	isHigh = 0;
	videoPlayCount = 0;
	videoScore = 0.0;
	playLength = 0.0;
	haveOriginalData = 0;

	if (js)
		LoadFromJson(js);
}

KolaVideo::~KolaVideo()
{
	deleteLocalVideoFile();
	Clear();
}

void KolaVideo::Clear() {
	for (size_t i=0, count = segmentList.size(); i < count; i++) {
		segmentList[i].Cancel();
//		delete segmentList[i];
	}

	segmentList.clear();
}

bool KolaVideo::UpdatePlayInfo(json_t *js)
{
	totalDuration = json_getreal(js, "totalDuration", 0.0);
	width         = json_geti(js, "width", 0);
	totalBlocks   = json_geti(js, "totalBlocks", 0);
	height        = json_geti(js, "height", 0);
	totalBytes    = json_geti(js, "totalBytes", 0);
	fps           = json_geti(js, "fps", 0);
	directPlayUrl = json_gets(js, "directPlayUrl", "");

	Clear();
	if (directPlayUrl == "") {
		json_t *sets, *value;
		sets = json_geto(js, "sets");
		json_array_foreach(sets, value) {
			//VideoSegment *seg = new VideoSegment(value);
			//segmentList.push_back(seg);
			segmentList.push_back(VideoSegment(value));
		}
	}

	return true;
}

bool KolaVideo::GetPlayInfo(void)
{
	std::string text;
	KolaClient *client = &KolaClient::Instance();
	bool ret = false;
	char buffer[128];

	if (client->UrlGet("", text, playUrl.c_str()) == false)
		return false;

	sprintf(buffer, "/video/getplayer?cid=%d", cid);
	if (client->UrlPost(buffer, text.c_str(), text) == true) {
		json_t *js;
		json_error_t error;

		js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		if (js) {
			ret = UpdatePlayInfo(js);
			json_decref(js);
		}
	}

	return ret;
}

bool KolaVideo::LoadFromJson(json_t *js)
{
	json_t *sub;

	name             = json_gets(js   , "name"           , "");
	playlistid       = json_gets(js   , "playlistid"     , "");
	pid              = json_gets(js   , "pid"            , "");
	vid              = json_gets(js   , "vid"            , "");
	cid              = json_geti(js   , "cid"            , 0);
	order            = json_geti(js   , "order"          , 0);
	isHigh           = json_geti(js   , "isHigh"         , 0);

	videoPlayCount   = json_geti(js   , "videoPlayCount" , 0);
	videoScore       = json_getreal(js, "videoScore"     , 0.0);
	playLength       = json_getreal(js, "playLength"     , 0.0);

	showName         = json_gets(js   , "showName"       , "");
	publishTime      = json_gets(js   , "publishTime"    , "");
	videoDesc        = json_gets(js   , "videoDesc"      , "");

	smallPicUrl      = json_gets(js   , "smallPicUrl"    , "");
	largePicUrl      = json_gets(js   , "largePicUrl"    , "");
	playUrl          = json_gets(js   , "playUrl"        , "");
	directPlayUrl    = json_gets(js   , "directPlayUrl"  , "");

	sub = json_geto(js, "script");
	if (sub) {
		Script.LoadFromJson(sub);
	}
#if 1
	haveOriginalData = json_geti(js   , "haveOriginalData", 0);
	sub = json_geto(js   , "originalData");

	if (directPlayUrl == "" && sub)
		UpdatePlayInfo(sub);
#endif

	return true;
}

void KolaVideo::deleteLocalVideoFile()
{
	if (localVideoFile != "") {
		unlink(localVideoFile.c_str());
		localVideoFile = "";
	}
}

std::string KolaVideo::GetVideoUrl(void)
{
	if (Script.Exists())
		return Script.Run();

	if (directPlayUrl == "" && haveOriginalData == false)
		GetPlayInfo();

	char buf[256];
	size_t count = segmentList.size();
	std::string text, ret;
	StringList videos;
	KolaClient *client =& KolaClient::Instance();

	if (count == 0)
		return directPlayUrl;

	for (size_t i = 0; i < count; i++) {
		VideoSegment *seg = &segmentList[i];
		seg->Start();
	}

	for (size_t i = 0; i < count; i++) {
		VideoSegment *seg = &segmentList[i];
		seg->Wait();
		videos << seg->realUrl;
	}

	text = "{\"sets\": [" + videos.ToString() + "]}";
	sprintf(buf, "/video/getplayer?step=3&cid=%d", cid);

	if (client->UrlPost(buf, text.c_str(), ret) == false)
		return "";

	return ret;
}

