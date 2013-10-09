#include <iostream>

#include "json.h"
#include "kola.hpp"
#include "base64.hpp"
#include "httplib.h"

bool KolaAlbum::LoadFromJson(json_t *js)
{
	albumName      = json_gets(js, "albumName"  , "");
	albumDesc      = json_gets(js, "albumDesc"  , "");
	vid            = json_geti(js, "vid"        , 0);
	pid            = json_geti(js, "pid"        , 0);
	playlistid     = json_geti(js, "playlistid" , 0);
	isHigh         = json_geti(js, "isHigh"     , 0);
	publishYear    = json_geti(js, "publishYear", 0);
	totalSet       = json_geti(js, "totalSet"   , 0);
	area           = json_gets(js, "area"       , "");

	videoPlayUrl   = json_gets(js, "videoPlayUrl"  , "");
	largePicUrl    = json_gets(js, "largePicUrl"   , "");
	smallPicUrl    = json_gets(js, "smallPicUrl"   , "");
	largeHorPicUrl = json_gets(js, "largeHorPicUrl", "");
	smallHorPicUrl = json_gets(js, "smallHorPicUrl", "");
	largeVerPicUrl = json_gets(js, "largeVerPicUrl", "");
	smallVerPicUrl = json_gets(js, "smallVerPicUrl", "");

#if 0
	std::cout << "largePicUrl: " << largePicUrl << std::endl;
	std::cout << "smallPicUrl: " << smallPicUrl << std::endl;
	std::cout << "largeHorPicUrl: " << largeHorPicUrl << std::endl;
	std::cout << "smallHorPicUrl : " << smallHorPicUrl << std::endl;
	std::cout << "largeVerPicUrl: " << largeVerPicUrl << std::endl;
	std::cout << "smallVerPicUrl: " << smallVerPicUrl << std::endl;
#endif

	dailyPlayNum    =json_geti   (js , "dailyPlayNum"    , 0);   // 每日播放次数
	weeklyPlayNum   =json_geti   (js , "weeklyPlayNum"   , 0);   // 每周播放次数
	monthlyPlayNum  =json_geti   (js , "monthlyPlayNum"  , 0);   // 每月播放次数
	totalPlayNum    =json_geti   (js , "totalPlayNum"    , 0);   // 总播放资料
	dailyIndexScore =json_getreal(js , "dailyIndexScore" , 0.0); // 每日指数

	//directors = json_gets(js, "directors", "");
	//actors = json_gets(js, "actors", "");
	//mainActors = json_gets(js, "mainActors", "");
	//categories = json_gets(js, "categories", "");

//	std::cout << "KolaAlbum:" << albumName << std::endl;
	return true;
}

bool KolaAlbum::GetVideo(void)
{
	std::string text;
	json_t *js;
	json_error_t error;
	KolaClient *client = &KolaClient::Instance();

	if (client->UrlGet("", text, videoPlayUrl.c_str()) == false)
		return false;

	if (client->UrlPost("/video/getplayer", text.c_str(), text) == false)
		return false;

	js = json_loads(text.c_str(), JSON_REJECT_DUPLICATES, &error);
	if (js == NULL)
		return false;

	bool ret = video.LoadFromJson(js);
	json_decref(js);

	return ret;
}

std::string &KolaAlbum::GetPictureUrl(enum PicType type)
{
	std::string &fileName = this->smallPicUrl;;
	KolaClient *client =& KolaClient::Instance();

	switch (type){
		case PIC_LARGE:
			fileName = this->largePicUrl; break;
		case PIC_SMALL:
			fileName = this->smallPicUrl; break;
		case PIC_LARGE_HOR:
			fileName = this->largeHorPicUrl; break;
		case PIC_SMALL_HOR:
			fileName = this->smallHorPicUrl; break;
		case PIC_LARGE_VER:
			fileName = this->largeVerPicUrl; break;
		case PIC_SMALL_VER:
			fileName = this->smallVerPicUrl; break;
		default:
			break;
	}

	return fileName;
}

Picture *KolaAlbum::GetPicture(enum PicType type) // 得到图片
{
	return NULL;
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

bool KolaVideo::LoadFromJson(json_t *js)
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

bool KolaVideo::GetPlayerUrl(size_t index, std::string &url)
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
	//std::cout << "Get: " << seg.url << std::endl;
	if (client->UrlGet("", text, seg.url.c_str()) == false)
		return false;

	text = base64encode(text);
	text = "{\"sets\": [" + seg.GetJsonStr(&text) + "]}";
	if (client->UrlPost("/video/getplayer?step=2", text.c_str(), text) == false)
		return false;

	js = json_loads(text.c_str(), JSON_REJECT_DUPLICATES, &error);
	if (js == NULL)
		return false;

	sets = json_geto(js, "sets");
	if (sets && json_is_array(sets) && json_array_size(sets) > 0) {
		json_t *u = json_array_get(sets, 0);
		if (u) {
			seg.realUrl = json_string_value(u);
			url = seg.realUrl;
			return true;
		}
	}

	//std::cout << seg.realUrl << std::endl;

	return false;
}

