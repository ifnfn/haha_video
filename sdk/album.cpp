#include <iostream>

#include "json.h"
#include "kola.hpp"
#include "base64.hpp"
#include "httplib.h"

KolaAlbum::KolaAlbum(json_t *js) {
	directVideos = false;
	LoadFromJson(js);
}

KolaAlbum::~KolaAlbum() {
	VideosClear();
}

void KolaAlbum::VideosClear() {
	for (int i=videos.size() - 1; i >= 0;i--)
		delete videos[i];

	videos.clear();
}

bool KolaAlbum::LoadFromJson(json_t *js)
{
	json_t *sources;
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

	//directors  = json_gets(js, "directors", "");
	//actors     = json_gets(js, "actors", "");
	//mainActors = json_gets(js, "mainActors", "");
	//categories = json_gets(js, "categories", "");
//	std::cout << "KolaAlbum:" << albumName << std::endl;

	sources = json_geto(js, "sources");

	if (sources) {
		json_t *v;
		directVideos = true;
		VideosClear();
		json_array_foreach(sources, v) {
			this->videos.push_back(new KolaVideo(v));
		}
	}

	return true;
}

bool KolaAlbum::Run(void)
{
	if (directVideos)
		return directVideos;

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

	VideosClear();
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

AlbumPage::AlbumPage()
{

}

AlbumPage::~AlbumPage(void)
{
	Clear();
}

void AlbumPage::CachePicture(enum PicType type) // 将图片加至线程队列，后台下载
{
	for (std::vector<KolaAlbum*>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		std::string &fileName = (*it)->GetPictureUrl(type);
		PutPicture(fileName);
	}
}

void AlbumPage::PutPicture(std::string fileName)
{
	if (fileName != "") {
		std::map<std::string, Picture*>::iterator it;

		it = pictureList.find(fileName);
		if (it == pictureList.end()) {
			Picture *pic = new Picture(fileName);
			pictureList.insert(std::pair<std::string, Picture*>(fileName, pic));
			pic->Start();
		}
	}
}

void AlbumPage::PutAlbum(KolaAlbum *album)
{
	if (album) {
		album->Start();
		albumList.push_back(album);
	}
}

KolaAlbum* AlbumPage::GetAlbum(int index)
{
	return albumList.at(index);
}

Picture* AlbumPage::GetPicture(std::string fileName)
{
	std::map<std::string, Picture*>::iterator it;

	it = pictureList.find(fileName);

	if (it != pictureList.end())
		return it->second;

	return NULL;
}

void AlbumPage::Clear()
{
	for (std::vector<KolaAlbum*>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		(*it)->Cancel();
		delete (*it);
	}

	albumList.clear();

	for (std::map<std::string, Picture*>::iterator it = pictureList.begin(); it != pictureList.end(); it++) {
		it->second->Cancel();
		delete it->second;
	}

	pictureList.clear();
}
