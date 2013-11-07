#include <iostream>
#include <unistd.h>

#include "kola.hpp"
#include "json.h"
#include "base64.hpp"

VideoSegment::VideoSegment()
{
	duration = 0;
	size = 0;
	video = NULL;
}

VideoSegment::VideoSegment(KolaVideo *video, json_t *js) {
	this->video = video;
	LoadFromJson(js);
}

VideoSegment::VideoSegment(std::string u, std::string n, double d, size_t s) {
	url = u;
	newfile = n;
	duration = d;
	size = s;
	video = NULL;
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

bool VideoSegment::Run()
{
	KolaClient *client =& KolaClient::Instance();
	std::string text;
	json_t *js, *sets;
	json_error_t error;
	char buffer[128];

	if (client == NULL) {
		while(1)
			printf("error\n");
	}

	if (client->UrlGet("", text, url.c_str()) == false)
		return false;

	realUrl = GetJsonStr(&text);

	return true;
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
		segmentList[i]->Cancel();
		delete segmentList[i];
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
			VideoSegment *seg = new VideoSegment(this, value);
			segmentList.push_back(seg);
		}
	}

	return true;
}

bool KolaVideo::GetPlayInfo(void)
{
	std::string text;
	json_t *js;
	json_error_t error;
	KolaClient *client = &KolaClient::Instance();
	char buffer[128];

	if (client->UrlGet("", text, playUrl.c_str()) == false)
		return false;

	sprintf(buffer, "/video/getplayer?cid=%d", cid);
	if (client->UrlPost(buffer, text.c_str(), text) == false)
		return false;

	js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js == NULL)
		return false;

	return UpdatePlayInfo(js);

	json_decref(js);

	return true;
}

bool KolaVideo::LoadFromJson(json_t *js)
{
	json_t *originalData;

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

#if 1
	haveOriginalData = json_geti(js   , "haveOriginalData", 0);
	originalData     = json_geto(js   , "originalData");

	if (directPlayUrl == "" && originalData)
		UpdatePlayInfo(originalData);
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
	if (directPlayUrl == "" && haveOriginalData == false)
		GetPlayInfo();

	char buf[256];
	size_t count = segmentList.size();
	std::string text;
	StringList videos;
	KolaClient *client =& KolaClient::Instance();

	if (count == 0)
		return directPlayUrl;

	for (size_t i = 0; i < count; i++) {
		VideoSegment *seg = segmentList[i];
		seg->Start();
	}

	for (size_t i = 0; i < count; i++) {
		VideoSegment *seg = segmentList[i];
		seg->Wait();
		videos << seg->realUrl;
	}

	text = "{\"sets\": [" + videos.ToString() + "]}";
	sprintf(buf, "/video/getplayer?step=2&cid=%d", cid);

	if (client->UrlPost(buf, text.c_str(), text) == false)
		return "";

	std::cout << text << std::endl;

	return text;
}

