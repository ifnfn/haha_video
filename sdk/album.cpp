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

bool KolaAlbum::GetVideos(void)
{
	std::string text;
	json_t *js, *videos, *v;
	json_error_t error;
	KolaClient *client = &KolaClient::Instance();
	char url[128];

	sprintf(url, "/video/getvideo?full=1&pid=%d", vid);

	if (client->UrlPost(url, NULL, text) == false)
		return false;

	js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js == NULL)
		return false;

	videos = json_geto(js, "videos");

	this->videos.clear();
	json_array_foreach(videos, v) {
		this->videos.push_back(KolaVideo(v));
	}

	json_decref(js);

	return true;
}

std::string &KolaAlbum::GetPictureUrl(enum PicType type)
{
	std::string &fileName = this->smallPicUrl;

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

bool KolaAlbum::Run() {
	GetVideos();
}


void AlbumPage::UpdateVideos(void)
{
	for (std::vector<KolaAlbum>::iterator it = begin(); it != end(); it++)
		it->Start();
}

void AlbumPage::CachePicture(enum PicType type) // 将图片加至线程队列，后台下载
{
	for (std::vector<KolaAlbum>::iterator it = begin(); it != end(); it++) {
		std::string &fileName = it->GetPictureUrl(type);
		if (fileName != "")
			picCache.Add(fileName);
	}
}

KolaAlbum& AlbumPage::GetAlbum(int index) {
	KolaAlbum &album = at(index);
	album.Wait();

	return album;
}


