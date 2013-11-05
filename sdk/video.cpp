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

bool VideoSegment::Run()
{
	std::string video_url;

	return GetVideoUrl(video_url);
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

	snprintf(buffer, 2047, "{\n\"url\":\"%s\",\n\"new\":\"%s\"\n}", newUrl->c_str(), newfile.c_str());

	return std::string(buffer);
}

bool VideoSegment::GetVideoUrl(std::string &player_url)
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

	//std::cout << "Get: " << url << std::endl;
	if (client->UrlGet("", text, url.c_str()) == false)
		return false;

	text = base64encode(text);
	text = "{\"sets\": [" + GetJsonStr(&text) + "]}";

	if (video)
		sprintf(buffer, "/video/getplayer?step=2&cid=%d", video->cid);
	else
		sprintf(buffer, "/video/getplayer?step=2");

	if (client->UrlPost(buffer, text.c_str(), text) == false)
		return false;

	js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js == NULL)
		return false;

	sets = json_geto(js, "sets");
	if (sets && json_is_array(sets) && json_array_size(sets) > 0) {
		json_t *u = json_array_get(sets, 0);
		if (u) {
			realUrl = json_string_value(u);
			player_url = realUrl;
			return true;
		}
	}

	std::cout << realUrl << std::endl;

	return false;
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

	if (client->UrlGet("", text, playUrl.c_str()) == false) {
		printf("wget %s error!\n", playUrl.c_str());
		return false;
	}

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

	haveOriginalData = json_geti(js   , "haveOriginalData", 0);
	originalData     = json_geto(js   , "originalData");

	if (directPlayUrl == "") {
		if (originalData)
			UpdatePlayInfo(originalData);
		else
			GetPlayInfo();
	}

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
	char buf[256];
	size_t count = segmentList.size();
	std::string ret, player_url;
	double max_duration = 0;

	if (count == 0)
		return directPlayUrl;
	else if (count == 1) {
		VideoSegment *seg = segmentList[0];
		seg->Start();
		seg->Wait();
		return seg->realUrl;
	}

	ret = "";
	for (size_t i=0; i < count;i++) {
		VideoSegment *seg = segmentList[i];

		if (seg->duration > max_duration)
			max_duration = seg->duration;
		seg->Start();
	}

	for (size_t i=0; i < count;i++) {
		VideoSegment *seg = segmentList[i];
		seg->Wait();
		sprintf(buf, "#EXTINF:%d,\n", (int)seg->duration);
		ret = ret + buf;
		ret = ret + seg->realUrl;
		ret = ret + "\n";
	}

	ret = ret + "#EXT-X-ENDLIST\n";

	sprintf(buf, "#EXTM3U\n#EXT-X-TARGETDURATION:%d\n", (int)max_duration);

	ret = buf + ret;

	if (count > 0) {
		deleteLocalVideoFile();
		char fileName[128];

		sprintf(fileName, "/tmp/video_%ld", random());
		FILE *fp = fopen(fileName, "w");

		if (fp) {
			fwrite(ret.c_str(), 1, ret.size(), fp);
			fclose(fp);
			localVideoFile = fileName;

			return localVideoFile;
		}
		else {
			KolaClient *client =& KolaClient::Instance();
			if (client->UrlPost("/video/urls", ret.c_str(), ret) == false)
				return "";

			return client->GetFullUrl("/video/urls" + ret);
		}
	}

	return ret;
}

bool KolaVideo::GetVideoUrl(std::string &video_url, size_t index)
{
	KolaClient *client =& KolaClient::Instance();
	std::string text;

	if (client == NULL)
		while(1) {
			printf("error\n");
		}
	if (index >= segmentList.size())
		return false;

	VideoSegment *seg = segmentList[index];
	if (seg)
		return seg->GetVideoUrl(video_url);

	return false;
}


