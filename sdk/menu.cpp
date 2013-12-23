#include <iostream>

#include "json.hpp"
#include "kola.hpp"
#include "http.hpp"

KolaMenu::KolaMenu() {
	cid = -1;
	PageId = -1;
	Language = "zh";
	PageSize = DEFAULT_PAGE_SIZE;
	albumCount = 0;

	prev = &page[0];
	cur = &page[1];
	next = &page[2];

	client = &KolaClient::Instance();
}

KolaMenu::KolaMenu(json_t *js)
{
	json_t *sub;
	PageSize   = DEFAULT_PAGE_SIZE;
	PageId     = -1;
	albumCount = 0;
	prev = &page[0];
	cur  = &page[1];
	next = &page[2];
	cid        = json_geti(js, "cid" , -1);
	json_gets(js, "name", name);

	client = &KolaClient::Instance();

	sub = json_geto(js, "filter");
	if (sub) {
		const char *key;
		json_t *values;
		json_object_foreach(sub, key, values) {
			json_t *v;
			string list;
			json_array_foreach(values, v)
				list = list + json_string_value(v) + ",";
//			printf("%s: %s\n", key, list.c_str());
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
	if (ret)
		quickFilter = name;

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
	int count = LowGetPage(cur, "vid", vid, PageSize);

	PageId = cur->pageId;

	if (PageId > 0)
		LowGetPage(prev, PageId - 1, PageSize);
	LowGetPage(next, PageId + 1, PageSize);

	for (int i=0; i<count; i++) {
		KolaAlbum *album = cur->GetAlbum(i);
		if (album && album->vid == vid)
			return PageId * PageSize + i;
	}

	return -1;
}

int KolaMenu::SeekByAlbumName(string name)
{
	CleanPage();
	int count = LowGetPage(cur, "albumName", name, PageSize);

	PageId = cur->pageId;

	if (PageId > 0)
		LowGetPage(prev, PageId - 1, PageSize);
	LowGetPage(next, PageId + 1, PageSize);

	for (int i=0; i<count; i++) {
		KolaAlbum *album = cur->GetAlbum(i);
		if (album && album->vid == name)
			return i;
	}

	return -1;
}

int KolaMenu::ParserJson(AlbumPage *page, string &text)
{
	int cnt = 0;
	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js) {
		albumCount = json_geti(js, "total", 0);
		page->pageId = (int)json_geti(js, "page", page->pageId);
		json_t *results = json_geto(js, "result");

		if (json_is_array(results)) {
			json_t *value;
			json_array_foreach(results, value) {
				page->PutAlbum(new KolaAlbum(value));
				cnt++;
			}
		}

		json_delete(js);
	}

	return cnt;
}

string KolaMenu::GetPostData()
{
	int count = 0;
	string body("{");
	string filter = Filter.GetJsonStr();
	string sort = Sort.GetJsonStr();

	if (quickFilter.size() > 0) {
		body = body + "\"quickFilter\": \"" + quickFilter + "\"";
		count++;
	}
	else if (filter.size() > 0) {
		body = body + filter;
		count++;
	}

	if (sort.size() > 0) {
		if (count)
			body = body + ",";
		body = body + sort;
	}

	body = body + "}";
//	cout << "Filter Body: " << body << endl;

	return body;
}

int KolaMenu::LowGetPage(AlbumPage *page, int pageId, int pageSize)
{
	char url[256];
	string text;

	string body = GetPostData();

	if (name.empty() or cid == -1)
		return 0;

	sprintf(url, "/video/list?page=%d&size=%d&cid=%d", pageId, pageSize, cid);
	if (client->UrlPost(url, body.c_str(), text) == true) {
		page->Clear();
		return ParserJson(page, text);
	}

	return 0;
}

int KolaMenu::LowGetPage(AlbumPage *page, string key, string value, int pageSize)
{
	char url[256];
	string text;

	string body = GetPostData();

	if (name.empty() or cid == -1)
		return 0;

	sprintf(url, "/video/list?&size=%d&cid=%d&key=%s&value=%s", pageSize, cid, key.c_str(), value.c_str());
	if (client->UrlPost(url, body.c_str(), text) == true) {
		page->Clear();
		return ParserJson(page, text);
	}

	return 0;
}

int KolaMenu::GetPage(AlbumPage &page, int pageNo)
{
	if (pageNo == -1)
		PageId++;
	else
		PageId = pageNo;

	return LowGetPage(&page, PageId, PageSize);
}

void KolaMenu::CleanPage()
{
	prev->Clear();
	cur->Clear();
	next->Clear();
}

KolaAlbum* KolaMenu::GetAlbum(size_t position)
{
	int page = (int)(position / PageSize);
	if (cur->pageId != page) {
		if (cur->pageId + 1 == page) {  // 下一页
			AlbumPage *tmp = prev;
			prev = cur;
			cur = next;
			next = tmp;
		}
		else if (cur->pageId - 1 == page) { // 向上一页
			AlbumPage *tmp = next;
			next = cur;
			cur = prev;
			prev = tmp;
		}
		else  // 不在三页中
			CleanPage();
		cur->Clear();
		LowGetPage(cur, page, PageSize);
#if 0
		if (next->pageId == page) {
			AlbumPage *tmp = prev;
			prev = cur;
			cur = next;
			next = tmp;
			next->Clear();
			LowGetPage(next, page + 1, PageSize);
		}
		else if (prev->pageId == page) {
			AlbumPage *tmp = next;
			next = cur;
			cur = prev;
			prev = tmp;
			prev->Clear();
			LowGetPage(prev, page - 1, PageSize);
		}
		else {
			CleanPage();
			if (page > 0)
				LowGetPage(prev, page - 1, PageSize);
			LowGetPage(cur, page, PageSize);
			LowGetPage(next, page + 1, PageSize);
		}
#endif
	}

	return cur->GetAlbum(position % PageSize);
}

CustomMenu::CustomMenu(string fileName)
{
	this->fileName = fileName;
	albumIdList.LoadFromFile(fileName);
	albumCount = albumIdList.size();
}

void CustomMenu::AlbumAdd(KolaAlbum *album)
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

void CustomMenu::AlbumRemove(KolaAlbum *album)
{
	if (album)
		AlbumRemove(album->vid);
}

void CustomMenu::AlbumRemove(string vid) {
	albumIdList.Remove(vid);
	albumCount = albumIdList.size();
	CleanPage();
}

size_t CustomMenu::GetAlbumCount() {
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

int CustomMenu::LowGetPage(AlbumPage *page, int pageId, int pageSize)
{
	string text;
	//int pos = pageId * pageSize;

	//text = albumIdList.ToString(pos, pageSize);
	text = albumIdList.ToString();
	if (text.size() > 0) {
		char buf[128];
		string url;
		string body = GetPostData();

		sprintf(buf, "video/list?page=%d&size=%d&vid=", pageId, pageSize);

		text = UrlEncode(text);
		url = buf + text;
		if (client->UrlPost(url, body.c_str(), text) == true) {
			page->Clear();
			return ParserJson(page, text);
		}
	}

	return 0;
}

