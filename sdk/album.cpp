#include <iostream>

#include "json.hpp"
#include "kola.hpp"
#include "base64.hpp"
#include "httplib.h"

#define VIDEO_COUNT 8
KolaAlbum::KolaAlbum(json_t *js)
{
	directVideos = false;
	videoPageSize = VIDEO_COUNT;
	videoPageId = -1;
	videoListUrl = NULL;
	LoadFromJson(js);
}

KolaAlbum::~KolaAlbum() {
	VideosClear();
	if (videoListUrl)
		json_delete(videoListUrl);
}

void KolaAlbum::VideosClear() {
	for (int i=videos.size() - 1; i >= 0;i--)
		delete videos[i];

	videos.clear();
}

size_t KolaAlbum::GetTotalSet() {
	if (totalSet == 0) {
		int old_size = videoPageSize;
		LowVideoGetPage(0, 0);
		videoPageSize = old_size;
		videoPageId = -1;
	}

	return totalSet;
}

size_t KolaAlbum::GetVideoCount()
{
	if (directVideos == false || totalSet == 0 || updateSet == 0) {
		int old_size = videoPageSize;
		LowVideoGetPage(0, 0);
		videoPageSize = old_size;
		videoPageId = -1;
	}

       return updateSet;
}

bool KolaAlbum::LowVideoGetPage(size_t pageNo, size_t pageSize)
{
	json_t *js = NULL, *videos, *v;
	if (pageNo == videoPageId)
		return true;

	if (videoListUrl) {
		ScriptCommand script;
		if (json_to_variant(videoListUrl, &script)) {
			json_error_t error;
			script.AddParams(pageNo);
			script.AddParams(pageSize);
			std::string text = script.Run();
			if (text != "")
				js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		}
	}

	if (js == NULL) {
		KolaClient *client = &KolaClient::Instance();
		char url_buffer[256];

		sprintf(url_buffer, "/video/getvideo?full=0&pid=%s&page=%ld&size=%ld", vid.c_str(), pageNo, pageSize);

		js = json_loadurl(url_buffer);
	}
	if (js == NULL)
		return false;

	updateSet = json_geti(js, "count", updateSet);
	updateSet = json_geti(js, "updateSet", updateSet);
	totalSet = json_geti(js, "totalSet", totalSet);

	videoPageId = pageNo;
	videoPageSize = pageSize;
	VideosClear();

	int x = 0;
	videos = json_geto(js, "videos");
	json_array_foreach(videos, v) {
		this->videos.push_back(new KolaVideo(v));
	}

	json_delete(js);

	return true;
}

bool KolaAlbum::LoadFromJson(json_t *js)
{
	json_t *sub;

	json_gets(js, "albumName"  , albumName);
	json_gets(js, "albumDesc"  , albumDesc);
	json_gets(js, "vid"        , vid);
	json_gets(js, "pid"        , pid);
	json_gets(js, "playlistid" , playlistid);
	cid            = json_geti(js, "cid"        , 0);
	isHigh         = json_geti(js, "isHigh"     , 0);
	publishYear    = json_geti(js, "publishYear", 0);
	totalSet       = json_geti(js, "totalSet"   , 0);
	updateSet      = json_geti(js, "updateSet"  , totalSet);

	json_gets(js, "area"          , area);
	json_gets(js, "videoPlayUrl"  , videoPlayUrl  );
	json_gets(js, "largePicUrl"   , largePicUrl   );
	json_gets(js, "smallPicUrl"   , smallPicUrl   );
	json_gets(js, "largeHorPicUrl", largeHorPicUrl);
	json_gets(js, "smallHorPicUrl", smallHorPicUrl);
	json_gets(js, "largeVerPicUrl", largeVerPicUrl);
	json_gets(js, "smallVerPicUrl", smallVerPicUrl);
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

	json_get_stringlist(js, "mainActors", &mainActors);
	json_get_stringlist(js, "directors", &directors);

	sub = json_geto(js, "videoListUrl");
	if (sub)
		videoListUrl = json_deep_copy(sub);

	//categories = json_gets(js, "categories", "");
//	std::cout << "KolaAlbum:" << albumName << std::endl;

	sub = json_geto(js, "sources");
	if (sub) {
		json_t *v;
		directVideos = true;
		VideosClear();
		json_array_foreach(sub, v) {
			this->videos.push_back(new KolaVideo(v));
		}
	}

	return true;
}

KolaVideo *KolaAlbum::GetVideo(int id)
{
	size_t pageNo = id / videoPageSize;
	size_t pos = id % videoPageSize;

	if (pageNo != videoPageId && directVideos == false)
		LowVideoGetPage(pageNo, videoPageSize);

	if (pos < videos.size())
		return videos[pos];

	return NULL;
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
	pageId = -1;
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
		albumList.push_back(album);
	}
}

KolaAlbum* AlbumPage::GetAlbum(int index)
{
	if (index < albumList.size() )
		return albumList.at(index);

	return NULL;
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
	pageId = -1;
	for (std::map<std::string, Picture*>::iterator it = pictureList.begin(); it != pictureList.end(); it++) {
		it->second->Cancel();
		delete it->second;
	}

	for (std::vector<KolaAlbum*>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		delete (*it);
	}

	pictureList.clear();
	albumList.clear();
}
