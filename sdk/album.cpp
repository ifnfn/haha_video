#include <iostream>

#include "json.hpp"
#include "kola.hpp"
#include "base64.hpp"
#include "resource.hpp"
#include "kolabase.hpp"

#define VIDEO_COUNT 16

KolaAlbum::KolaAlbum()
{
	menu = NULL;
	publishYear = 0;
	dailyPlayNum = 0;
	totalPlayNum = 0;
	Score = 0.0;
	order = 0;
	updateTime = 0;
	menu = NULL;
	directVideos = false;
	videoPageSize = VIDEO_COUNT;
	videoPageId = -1;
	playIndex = 0;
}

KolaAlbum::~KolaAlbum() {
	VideosClear();
}

void KolaAlbum::VideosClear() {
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
	Variant* var = NULL;

	if (pageNo == videoPageId)
		return true;

	if (SourceList.size() > 0) {
		map<string, Variant>::iterator it = SourceList.find(CurrentSource);

		if (it != SourceList.end())
			var = &it->second;
		else
			var = &SourceList.begin()->second;
	}

	if (var) {
		json_error_t error;
		var->AddParams((int)pageNo);
		var->AddParams((int)pageSize);
		string text = var->GetString();
		var->DelParams(2);
		if (not text.empty())
			js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	}

	if (js == NULL) {
		char url_buffer[256];

		sprintf(url_buffer, "/video/getvideo?full=0&pid=%s&page=%lu&size=%lu", vid.c_str(), pageNo, pageSize);

		js = json_loadurl(url_buffer);
	}
	if (js == NULL)
		return false;

	updateSet = json_geti(js, "count", updateSet);
	updateSet = json_geti(js, "updateSet", updateSet);
	totalSet  = json_geti(js, "totalSet", totalSet);

	videoPageId = pageNo;
	videoPageSize = pageSize;
	VideosClear();

	videos = json_geto(js, "videos");
	json_array_foreach(videos, v) {
		KolaVideo video;
		video.Parser(v);
		this->videoList.push_back(video);
	}

	json_delete(js);

	return true;
}

void KolaAlbum::Parser(json_t *js)
{
	json_t *sub;

	json_gets(js, "albumName"  , albumName);
	json_gets(js, "albumDesc"  , albumDesc);
	json_gets(js, "vid"        , vid);
	cid            = (int)json_geti(js, "cid"        , 0);
	isHigh         = (int)json_geti(js, "isHigh"     , 0);
	publishYear    = (int)json_geti(js, "publishYear", 0);
	totalSet       =      json_geti(js, "totalSet"   , 0);
	updateSet      =      json_geti(js, "updateSet"  , totalSet);

	json_gets(js, "area"          , area);
	json_gets(js, "videoPlayUrl"  , videoPlayUrl  );
	json_gets(js, "largePicUrl"   , largePicUrl   );
	json_gets(js, "smallPicUrl"   , smallPicUrl   );
	json_gets(js, "largeHorPicUrl", largeHorPicUrl);
	json_gets(js, "smallHorPicUrl", smallHorPicUrl);
	json_gets(js, "largeVerPicUrl", largeVerPicUrl);
	json_gets(js, "smallVerPicUrl", smallVerPicUrl);
	json_gets(js, "Number"        , Number);

#if 0
	cout << "largePicUrl: " << largePicUrl << endl;
	cout << "smallPicUrl: " << smallPicUrl << endl;
	cout << "largeHorPicUrl: " << largeHorPicUrl << endl;
	cout << "smallHorPicUrl : " << smallHorPicUrl << endl;
	cout << "largeVerPicUrl: " << largeVerPicUrl << endl;
	cout << "smallVerPicUrl: " << smallVerPicUrl << endl;
#endif

	updateTime   = (time_t)json_geti(js, "updateTime", 0);
	dailyPlayNum = (int)json_geti   (js, "dailyPlayNum", 0);   // 日播放次数
	totalPlayNum = (int)json_geti   (js, "totalPlayNum", 0);   // 总播放次数
	Score        = json_getreal     (js, "Score" , 0.0);       // 得分

	json_get_stringlist(js, "mainActors", &mainActors);
	json_get_stringlist(js, "directors", &directors);

	json_get_variant(js, "epgInfo", &EpgInfo);
	sub = json_geto(js, "engine");
	if (sub) {
		const char *key;
		json_t *values;

		SourceList.clear();
		json_object_foreach(sub, key, values)
			SourceList.insert(pair<string, Variant>(key, Variant(values)));
	}

	sub = json_geto(js, "sources");
	if (sub) {
		json_t *v;
		directVideos = true;
		VideosClear();
		json_array_foreach(sub, v) {
			KolaVideo video;
			video.Parser(v);
			this->videoList.push_back(video);
		}
	}
}

size_t KolaAlbum::GetSource(StringList &sources) // 获取节目的节目来源列表
{
	map<string, Variant>::iterator it;

	for (it=SourceList.begin(); it != SourceList.end(); it++) {
		sources.Add(it->first);
	}

	return sources.size();
}

bool KolaAlbum::SetSource(string source)      // 设置节目来源，为""时，使用默认来源
{
	map<string, Variant>::iterator it = SourceList.find(source);

	if (it != SourceList.end()) {
		this->CurrentSource = source;
		videoPageId = -1;
		VideosClear();
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
		return &videoList[pos];

	return NULL;
}

KolaEpg *KolaAlbum::NewEPG()
{
	if (not EpgInfo.Empty()) {
		KolaEpg *epg = new KolaEpg(EpgInfo);
		epg->SetPool(client->threadPool);

		return epg;
	}

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
	if (type != PIC_DISABLE) {
		string &fileName = GetPictureUrl(type);

		if (not fileName.empty()) {
			picture.Clear();
			return picture.GetResource(client->resManager, fileName) != NULL;
		}
	}

	return false;
}

AlbumPage::AlbumPage()
{
	pageId = -1;
	pictureCount = 0;
	menu = NULL;
	client = &KolaClient::Instance();
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

void AlbumPage::PutAlbum(KolaAlbum album)
{
	mutex.lock();

	album.menu = menu;
	albumList.push_back(album);

	mutex.unlock();
}

KolaAlbum* AlbumPage::GetAlbum(size_t index)
{
	KolaAlbum *album = NULL;

	mutex.lock();

	if (index < albumList.size() )
		album = &albumList.at(index);

	mutex.unlock();

	return album;
}

size_t AlbumPage::CachePicture(enum PicType type) // 将图片加至线程队列，后台下载
{
	pictureCount = 0;

	if (menu == NULL || menu->PictureCacheType == PIC_DISABLE)
		return 0;

	mutex.lock();
	for (vector<KolaAlbum>::iterator it = albumList.begin(); it != albumList.end(); it++) {
		string &url = (*it).GetPictureUrl(type);
		if (not url.empty()) {
			client->resManager->GetResource(url);

			pictureCount++;
		}
	}
	mutex.unlock();

	return pictureCount;
}

void AlbumPage::Clear()
{
	Task::Reset();

	mutex.lock();

	if (menu && menu->PictureCacheType != PIC_DISABLE) {
		for (vector<KolaAlbum>::iterator it = albumList.begin(); it != albumList.end(); it++) {
			string &url = (*it).GetPictureUrl(menu->PictureCacheType);
			if (not url.empty())
				client->resManager->RemoveResource(url);
		}
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
	list<KolaAlbum*>::iterator it;
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

size_t PictureIterator::size()
{
	return albums.size();
}
