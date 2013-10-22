#include <iostream>

#include "json.h"
#include "kola.hpp"
#include "base64.hpp"
#include "httplib.h"

KolaAlbum::KolaAlbum(json_t *js) {
	LoadFromJson(js);
}

KolaAlbum::~KolaAlbum() {
	for (size_t i=0, count=videos.size(); i < count;i++)
		delete videos[i];

	videos.clear();
}

bool KolaAlbum::LoadFromJson(json_t *js)
{
	albumName      = json_gets(js, "albumName"  , "");
	albumDesc      = json_gets(js, "albumDesc"  , "");
	cid            = json_geti(js, "cid"        , 0);
	vid            = json_gets(js, "vid"        , "");
	pid            = json_gets(js, "pid"        , "");
	playlistid     = json_gets(js, "playlistid" , "");
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
	std::string url;

	url = "/video/getvideo?full=1&pid=" + vid;

	if (client->UrlPost(url, NULL, text) == false)
		return false;

	js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js == NULL)
		return false;

	videos = json_geto(js, "videos");

	this->videos.clear();
	json_array_foreach(videos, v) {
		this->videos.push_back(new KolaVideo(v));
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
	return GetVideos();
}


AlbumPage::~AlbumPage(void)
{
	for (std::vector<KolaAlbum>::iterator it = albumList.begin(); it != albumList.end(); it++)
		it->Wait();

	for (std::map<std::string, Picture>::iterator it = pictureList.begin(); it != pictureList.end(); it++) {
		it->second.Wait();
	}
}

void AlbumPage::UpdateVideos(void)
{
	for (std::vector<KolaAlbum>::iterator it = albumList.begin(); it != albumList.end(); it++)
		it->Start();
}

void AlbumPage::CachePicture(enum PicType type) // 将图片加至线程队列，后台下载
{
	for (std::vector<KolaAlbum>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		std::string &fileName = it->GetPictureUrl(type);
		PutPicture(fileName);
	}
}

void AlbumPage::PutPicture(std::string fileName)
{
	if (fileName != "") {
		std::pair<std::map<std::string, Picture>::iterator, bool> ret;
		ret = pictureList.insert(std::pair<std::string, Picture>(fileName, Picture(fileName)));
		ret.first->second.Start();
	}
}

void AlbumPage::PutAlbum(KolaAlbum album)
{
	//albumList.push_back(album).Start();
	albumList.insert(albumList.end(), album)->Start();
}

KolaAlbum& AlbumPage::GetAlbum(int index)
{
	KolaAlbum &album = albumList.at(index);
	album.Wait();

	return album;
}

Picture& AlbumPage::GetPicture(std::string fileName)
{
	std::map<std::string, Picture>::iterator it;

	it = pictureList.find(fileName);

	if (it != pictureList.end()) {
		it->second.Wait();
		return it->second;
	}
	else {
		Picture pic(fileName);

	}

	throw std::invalid_argument(fileName);
}

void AlbumPage::Clear()
{
	pictureList.clear();
	albumList.clear();
}
