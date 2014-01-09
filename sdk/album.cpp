#include <iostream>

#include "json.hpp"
#include "kola.hpp"
#include "base64.hpp"
#include "resource.hpp"

#define VIDEO_COUNT 8

KolaAlbum::KolaAlbum(json_t *js)
{
	menu = NULL;
	directVideos = false;
	videoPageSize = VIDEO_COUNT;
	videoPageId = -1;
	videoListUrl = NULL;
	LoadFromJson(js);
}

KolaAlbum::~KolaAlbum() {
	VideosClear();
	if (videoListUrl) {
		json_delete(videoListUrl);
		videoListUrl = NULL;
	}
}

void KolaAlbum::VideosClear() {
	size_t z = videoList.size();
	for (int i=0; i < z; i++)
		delete videoList[i];

	videoList.clear();
}

size_t KolaAlbum::GetTotalSet() {
	if (totalSet == 0) {
		size_t old_size = videoPageSize;
		LowVideoGetPage(0, 0);
		videoPageSize = old_size;
		videoPageId = -1;
	}

	return totalSet;
}

size_t KolaAlbum::GetVideoCount()
{
	if (directVideos == false || totalSet == 0 || updateSet == 0) {
		size_t old_size = videoPageSize;
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
			script.AddParams((int)pageNo);
			script.AddParams((int)pageSize);
			string text = script.Run();
			if (text != "")
				js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		}
	}

	if (js == NULL) {
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

	videos = json_geto(js, "videos");
	json_array_foreach(videos, v) {
		this->videoList.push_back(new KolaVideo(v));
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
	cid            =  (int)json_geti(js, "cid"        , 0);
	isHigh         =  (int)json_geti(js, "isHigh"     , 0);
	publishYear    =  (int)json_geti(js, "publishYear", 0);
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
	cout << "largePicUrl: " << largePicUrl << endl;
	cout << "smallPicUrl: " << smallPicUrl << endl;
	cout << "largeHorPicUrl: " << largeHorPicUrl << endl;
	cout << "smallHorPicUrl : " << smallHorPicUrl << endl;
	cout << "largeVerPicUrl: " << largeVerPicUrl << endl;
	cout << "smallVerPicUrl: " << smallVerPicUrl << endl;
#endif

	dailyPlayNum    = (int)json_geti   (js , "dailyPlayNum"    , 0);   // 每日播放次数
	weeklyPlayNum   = (int)json_geti   (js , "weeklyPlayNum"   , 0);   // 每周播放次数
	monthlyPlayNum  = (int)json_geti   (js , "monthlyPlayNum"  , 0);   // 每月播放次数
	totalPlayNum    = (int)json_geti   (js , "totalPlayNum"    , 0);   // 总播放资料
	dailyIndexScore = (int)json_getreal(js , "dailyIndexScore" , 0.0); // 每日指数

	json_get_stringlist(js, "mainActors", &mainActors);
	json_get_stringlist(js, "directors", &directors);

	sub = json_geto(js, "videoListUrl");
	if (sub)
		videoListUrl = json_deep_copy(sub);

	sub = json_geto(js, "sources");
	if (sub) {
		json_t *v;
		directVideos = true;
		VideosClear();
		json_array_foreach(sub, v) {
			this->videoList.push_back(new KolaVideo(v));
		}
	}

	return true;
}

KolaVideo *KolaAlbum::GetVideo(size_t id)
{
	size_t pageNo = id / videoPageSize;
	size_t pos = id % videoPageSize;

	if (pageNo != videoPageId && directVideos == false)
		LowVideoGetPage(pageNo, videoPageSize);

	if (pos < videoList.size())
		return videoList[pos];

	return NULL;
}

string &KolaAlbum::GetPictureUrl(enum PicType type)
{
	string &fileName = this->smallPicUrl;

	if (type == PIC_AUTO && menu)
		type = menu->PictureCacheType;

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

bool KolaAlbum::GetPictureFile(FileResource& picture, enum PicType type)
{
	string &fileName = GetPictureUrl(type);

	if (not fileName.empty()) {
		KolaClient &kola = KolaClient::Instance();
		return kola.resManager->GetFile(picture, fileName);
	}

	return false;
}

AlbumPage::AlbumPage()
{
	pageId = -1;
	pictureCount = 0;
	menu = NULL;
	CachePcitureType = PIC_AUTO;
}

AlbumPage::~AlbumPage(void)
{
	Clear();
}

void AlbumPage::Run(void)
{
	if (menu && pageId >= 0) {
		menu->LowGetPage(this, pageId, menu->GetPageSize());
		CachePicture(menu->PictureCacheType);
	}
}

size_t AlbumPage::CachePicture(enum PicType type) // 将图片加至线程队列，后台下载
{
	pictureCount = 0;
	KolaClient &kola = KolaClient::Instance();

	mutex.lock();
	CachePcitureType = type;

	for (vector<KolaAlbum*>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		string &url = (*it)->GetPictureUrl(type);
		if (not url.empty()) {
			Resource *res = kola.resManager->GetResource(url);

			if (res) {
				res->score = score;
				res->DecRefCount();
			}
			pictureCount++;
		}
	}
	mutex.unlock();

	return pictureCount;
}

void AlbumPage::UpdateCache()
{
	KolaClient &kola = KolaClient::Instance();

	mutex.lock();

	for (vector<KolaAlbum*>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		string &url = (*it)->GetPictureUrl(CachePcitureType);
		if (not url.empty()) {
			Resource *res = kola.resManager->FindResource(url);
			if (res) {
				res->score = score;
			}
		}
	}

	mutex.unlock();
}

void AlbumPage::PutAlbum(KolaAlbum *album)
{
	mutex.lock();
	if (album) {
		album->menu = menu;
		albumList.push_back(album);
	}
	mutex.unlock();
}

KolaAlbum* AlbumPage::GetAlbum(size_t index)
{
	KolaAlbum *album = NULL;

	mutex.lock();

	if (index < albumList.size() )
		album = albumList.at(index);

	mutex.unlock();

	return album;
}

void AlbumPage::Clear()
{
	KolaClient &kola = KolaClient::Instance();
	Task::Reset();

	mutex.lock();
	for (vector<KolaAlbum*>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		string &url = (*it)->GetPictureUrl(CachePcitureType);
		if (not url.empty()) {
			Resource *res = kola.resManager->FindResource(url);
			if (res) {
				res->score = 255;
				if (kola.threadPool->removeTask(res))
					kola.resManager->RemoveResource(res);
			}
		}
		delete (*it);
	}

	albumList.clear();
	pageId = -1;
	mutex.unlock();
}

PictureIterator::PictureIterator(AlbumPage *page, enum PicType type)
{
	this->page = page;
	this->type = type;

	for (int i = 0; i < page->Count(); i++) {
		KolaAlbum *album = page->GetAlbum(i);
		album->order = i;
		albums.push_back(album);
	}
}

int PictureIterator::Get(FileResource &picture)
{
	std::list<KolaAlbum*>::iterator it;
	for (it = albums.begin(); it != albums.end();) {
		KolaAlbum* album = *it;
		if (album->GetPictureFile(picture, type) == true) {
			if (picture.isCached()) {
				albums.erase(it);
				return album->order;
			}
			it++;
		}
		else
			albums.erase(it++);
	}

	return -1;
}

size_t PictureIterator::size() {return albums.size();}
