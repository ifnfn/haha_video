#include <iostream>

#include "kola.hpp"
#include "json.h"
#include "base64.hpp"

VideoSegment::VideoSegment()
{
	duration = 0;
	size = 0;
}

VideoSegment::VideoSegment(json_t *js) {
	LoadFromJson(js);
}

VideoSegment::VideoSegment(std::string u, std::string n, double d, size_t s) {
	url = u;
	newfile = n;
	duration = d;
	size = s;
}

VideoSegment::~VideoSegment() { }

bool VideoSegment::Run() {
	std::string video_url;

	return GetVideoUrl(video_url);
}

bool VideoSegment::LoadFromJson(json_t *js)
{
	url = json_gets(js, "url", "");
	newfile = json_gets(js, "new", "");
	duration = json_getreal(js, "duration", 0.0);
	size = json_geti(js, "size", 0);

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

	if (client == NULL) {
		while(1)
			printf("error\n");
	}

	//std::cout << "Get: " << url << std::endl;
	if (client->UrlGet("", text, url.c_str()) == false)
		return false;

	text = base64encode(text);
	text = "{\"sets\": [" + GetJsonStr(&text) + "]}";
	if (client->UrlPost("/video/getplayer?step=2", text.c_str(), text) == false)
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

	//std::cout << realUrl << std::endl;

	return false;
}

bool KolaVideo::UpdatePlayInfo(json_t *js)
{
	json_t *sets, *value;
	if (json_geto(js, "sets") == NULL)
		return false;

	totalDuration = json_getreal(js, "totalDuration", 0.0);
	width         = json_geti(js, "width", 0);
	totalBlocks   = json_geti(js, "totalBlocks", 0);
	height        = json_geti(js, "height", 0);
	totalBytes    = json_geti(js, "totalBytes", 0);
	fps           = json_geti(js, "fps", 0);

	sets = json_geto(js, "sets");

	clear();
	json_array_foreach(sets, value)
		push_back(VideoSegment(value));

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

	if (album)
		sprintf(buffer, "/video/getplayer?cid=%d", album->cid);
	else
		sprintf(buffer, "/video/getplayer");

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

	name           = json_gets(js    , "name"           , "");
	playlistid     = json_geti(js    , "playlistid"     , 0);
	pid            = json_geti(js    , "pid"            , 0);
	vid            = json_geti(js    , "vid"            , 0);
	order          = json_geti(js    , "order"          , 0);
	isHigh         = json_geti(js    , "isHigh"         , 0);

	videoPlayCount = json_geti(js    , "videoPlayCount" , 0);
	videoScore     = json_getreal(js , "videoScore"     , 0.0);
	playLength     = json_getreal(js , "playLength"     , 0.0);

	showName       = json_gets(js    , "showName"       , "");
	publishTime    = json_gets(js    , "publishTime"    , "");
	videoDesc      = json_gets(js    , "videoDesc"      , "");

	smallPicUrl    = json_gets(js    , "smallPicUrl"    , "");
	largePicUrl    = json_gets(js    , "largePicUrl"    , "");
	playUrl        = json_gets(js    , "playUrl"        , "");
	haveOriginalData = json_geti(js  , "haveOriginalData", 0);
	originalData   = json_geto(js    , "originalData");

	if (originalData)
		UpdatePlayInfo(originalData);
	else
		GetPlayInfo();

	return true;
}

std::string KolaVideo::GetVideoUrl(void)
{
	char buf[256];
	size_t count = size();
	std::string ret, player_url;
	double max_duration = 0;

	ret = "#EXTM3U\n";
	ret = ret + "#EXT-X-TARGETDURATION:";

	ret = "";
	for (size_t i=0; i < count;i++) {
		VideoSegment &seg = at(i);

		if (seg.duration > max_duration)
			max_duration = seg.duration;
		seg.Start();
	}

	for (size_t i=0; i < count;i++) {
		VideoSegment &seg = at(i);
		seg.Wait();
		sprintf(buf, "#EXTINF:%d,\n", (int)seg.duration);
		ret = ret + buf;
		ret = ret + seg.realUrl;
		ret = ret + "\n";
	}

	ret = ret + "#EXT-X-ENDLIST\n";

	sprintf(buf, "#EXTM3U\n#EXT-X-TARGETDURATION:%d\n", (int)max_duration);

	ret = buf + ret;

	return ret;
}

bool KolaVideo::GetVideoUrl(std::string &video_url, size_t index)
{
	KolaClient *client =& KolaClient::Instance();
	std::string text;
	json_t *js, *sets;
	json_error_t error;

	if (client == NULL)
		while(1) {
			printf("error\n");
		}
	if (index >= size())
		return false;

	VideoSegment &seg = at(index);

	return seg.GetVideoUrl(video_url);
	//std::cout << seg.realUrl << std::endl;

	return false;
}


