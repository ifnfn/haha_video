#include <iostream>

#include "json.hpp"
#include "kola.hpp"
#include "http.hpp"

void KolaMenu::init()
{
	cid = -1;
	PageId = -1;
	PageSize = DEFAULT_PAGE_SIZE;
	albumCount = 0;
	PictureCacheType = PIC_LARGE;

	cur = &pageCache[0];
	for (int i=0; i < PAGE_CACHE; i++)
		pageCache[i].SetMenu(this);

	client = &KolaClient::Instance();
}

KolaMenu::KolaMenu()
{
	init();
}

void KolaMenu::Parser(json_t *js)
{
	json_t *sub;
	init();

	cid = json_geti(js, "cid" , -1);
	json_gets(js, "name", name);

	sub = json_geto(js, "filter");
	if (sub) {
		const char *key;
		json_t *values;
		json_object_foreach(sub, key, values) {
			json_t *v;
			string list;
			json_array_foreach(values, v)
				list = list + json_string_value(v) + ",";
			this->Filter.filterKey.insert(pair<string, FilterValue>(key, FilterValue(list)));
		}
	}

	sub = json_geto(js, "sort");
	if (sub) {
		json_t *v;
		string list;
		json_array_foreach(sub, v)
			list = list + json_string_value(v) + ",";
		this->Sort.Split(list);
	}

	sub = json_geto(js, "quickFilters");
	if (sub) {
		json_t *v;
		json_array_foreach(sub, v) {
			const char *s = json_string_value(v);
			if (s) {
				quickFilters << s;
			}
		}
	}
}

bool KolaMenu::SetQuickFilter(string name)
{
	bool ret = quickFilters.Find(name) || name.empty();
	if (ret) {
		quickFilter = name;
		CleanPage();
	}

	return ret;
}

size_t KolaMenu::GetAlbumCount()
{
	AlbumPage page;
	LowGetPage(&page, 0, 0);
	return albumCount;
}

int KolaMenu::SeekByAlbumId(string vid)
{
	CleanPage();
	cur = &this->pageCache[0];
	int count = LowGetPage(cur, "vid", vid, PageSize);

	PageId = cur->pageId;

	for (int i=0; i<count; i++) {
		IAlbum *album = cur->GetAlbum(i);
		if (album && album->vid == vid)
			return PageId * PageSize + i;
	}

	return -1;
}

int KolaMenu::SeekByAlbumName(string name)
{
	CleanPage();
	cur = &this->pageCache[0];
	int count = LowGetPage(cur, "albumName", name, PageSize);

	PageId = cur->pageId;

	for (int i=0; i<count; i++) {
		IAlbum *album = cur->GetAlbum(i);
		if (album && album->vid == name)
			return i;
	}

	return -1;
}

int KolaMenu::ParserFromUrl(AlbumPage *page, string &url)
{
	int cnt = 0;
	json_error_t error;
	string text;

	string body = GetPostData();
	if (client->UrlPost(url, body.c_str(), text) == true) {
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		if (js) {
			albumCount = json_geti(js, "total", 0);
			page->pageId = (int)json_geti(js, "page", page->pageId);
			json_t *results = json_geto(js, "result");

			if (json_is_array(results)) {
				json_t *value;
				json_array_foreach(results, value) {
					KolaAlbum *album = new KolaAlbum();
					album->SetSource(client->DefaultVideoSource);
					album->Parser(value);
					page->PutAlbum(album);
					cnt++;
				}
			}

			json_delete(js);
		}
	}

	return cnt;
}

void KolaMenu::FilterAdd(string key, string value)
{
	Filter.KeyAdd(key, value);
	CleanPage();
}

void KolaMenu::FilterRemove(string key)
{
	Filter.KeyAdd(key, "");
	CleanPage();
}

void KolaMenu::SetSort(string v, string s)
{
	Sort.Set(v, s);
	CleanPage();
}

void KolaMenu::SetPageSize(int size)
{
	PageSize = size;
	CleanPage();
}

string KolaMenu::GetPostData()
{
	int count = 0;
	string body("{");
	string filter = Filter.GetJsonStr();
	string sort = Sort.GetJsonStr();

	if (quickFilter.size() > 0) {
		body += "\"quickFilter\": \"" + quickFilter + "\"";
		count++;
	}
	else if (filter.size() > 0) {
		body += filter;
		count++;
	}

	if (sort.size() > 0) {
		if (count)
			body += ",";
		body += sort;
		count++;
	}

	KolaArea area;
	if (client->GetArea(area)) {
		if (count)
			body += ", ";
		body += area.toJson();
		count++;
	}

	if (not basePosData.empty()) {
		if (count)
			body += ",";
		body += basePosData;
		count++;
	}

	body = body + "}";
	//cout << "Filter Body: " << body << endl;

	return body;
}

int KolaMenu::LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize)
{
	char buf[256];
	string url;

	if (name.empty() or cid == -1)
		return 0;

	sprintf(buf, "/video/list?full=0&page=%ld&size=%ld&cid=%ld", pageId, pageSize, cid);
	url = buf;

	return ParserFromUrl(page, url);
}

int KolaMenu::LowGetPage(AlbumPage *page, string key, string value, size_t pageSize)
{
	char buf[256];
	string url;

	if (name.empty() or cid == -1)
		return 0;

	sprintf(buf, "/video/list?&full=0&size=%ld&cid=%ld&key=%s&value=%s",
		pageSize,
		cid,
		key.c_str(),
		value.c_str());

	url = buf;

	return ParserFromUrl(page, url);
}

AlbumPage &KolaMenu::GetPage(int pageNo)
{
	if (pageNo == -1) { // 下一页
		pageNo = PageId + 1;
	}

	return *updateCache(pageNo);
}

AlbumPage* KolaMenu::updateCache(int pos)
{
	int start = 0, end = 0;

	if (cur && pos == cur->pageId)
		return cur;
	else if (pos > PageId) { // 向后
		start = pos + 1;
		end = pos + PAGE_CACHE / 2;
	}
	else if (pos < PageId) { // 向后
		start = (int)pos - PAGE_CACHE / 2;
		end = pos - 1;
	}
	if (start < 0) start = 0;

	PageId = pos;

	// 更新当前页
	cur = &pageCache[pos % PAGE_CACHE];
	if (cur->pageId != PageId) {
		cur->Clear();
		cur->pageId = pos;
		cur->Start(true);
	}
	cur->Wait();

	for (int i = start; i <= end; i++) {
		int x = i % PAGE_CACHE;
		if (pageCache[x].pageId != i) {
			pageCache[x].Clear();
			pageCache[x].pageId = i;
			pageCache[x].Start(false);
		}
	}

	return cur;
}

IAlbum* KolaMenu::GetAlbum(size_t position)
{
	int pos = (int)position / PageSize;

	cur = updateCache(pos);
	return cur->GetAlbum(position % PageSize);
}

void KolaMenu::CleanPage()
{
	for (int i=0; i < PAGE_CACHE; i++) {
		pageCache[i].Clear();
	}
	cur = NULL;
	PageId = -1;
}

CustomMenu::CustomMenu(string fileName, bool CheckFailure)
{
	this->fileName = fileName;
	this->cid = -1;
	albumIdList.LoadFromFile(fileName);
	if (CheckFailure)
		RemoveFailure();
	albumCount = albumIdList.size();
}

void CustomMenu::RemoveFailure() // 移除失效的节目
{
	string text;
	string vids = albumIdList.ToString();
	if (vids.empty())
		return;

	KolaClient& kola = KolaClient::Instance();
	if (kola.UrlPost("video/vidcheck", vids.c_str(), text) == true) {
		json_error_t error;
		json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
		if (js) {
			json_t *v;
			json_array_foreach(js, v) {
				if (json_is_string(v)) {
					const char *vid = json_string_value(v);
					albumIdList.Remove(vid);
				}
			}

			json_decref(js);
		}
	}
}

void CustomMenu::AlbumAdd(IAlbum *album)
{
	if (album)
		AlbumAdd(album->vid);
}

void CustomMenu::AlbumAdd(string vid)
{
	CleanPage();
	albumIdList.Add(vid);
	albumCount = albumIdList.size();
}

void CustomMenu::AlbumRemove(IAlbum *album)
{
	if (album)
		AlbumRemove(album->vid);
}

void CustomMenu::AlbumRemove(string vid)
{
	albumIdList.Remove(vid);
	albumCount = albumIdList.size();
	CleanPage();
}

size_t CustomMenu::GetAlbumCount()
{
	albumCount = albumIdList.size();
	return albumCount;
}

bool CustomMenu::SaveToFile(string otherFile)
{
	if (not otherFile.empty())
		return albumIdList.SaveToFile(otherFile);
	else
		return albumIdList.SaveToFile(fileName);
}

int CustomMenu::LowGetPage(AlbumPage *page, size_t pageId, size_t pageSize)
{
	string text = albumIdList.ToString();
	if (not text.empty()) {
		char buf[128];
		string url;

		sprintf(buf, "video/list?full=0&page=%ld&size=%ld", pageId, pageSize);
		url = buf;

		basePosData = "\"vid\" : \"" + text + "\"";

		return ParserFromUrl(page, url);
	}

	return 0;
}

int CustomMenu::LowGetPage(AlbumPage *page, string key, string value, size_t pageSize)
{
	string text = albumIdList.ToString();

	if (not text.empty()) {
		char buf[256];
		string url;

		sprintf(buf, "/video/list?&full=0&size=%ld&key=%s&value=%s",
				pageSize,
				key.c_str(),
				value.c_str()
			);

		url = buf;

		basePosData = "\"vid\" : \"" + text + "\"";

		return ParserFromUrl(page, url);
	}

	return 0;
}

