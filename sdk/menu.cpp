#include <iostream>

#include "json.hpp"
#include "kola.hpp"
#include "httplib.h"

KolaMenu::KolaMenu() {
	cid = -1;
	PageId = -1;
	Language = "zh";
	//quickFilter = "";
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
			std::string list;
			json_array_foreach(values, v)
				list = list + json_string_value(v) + ",";
			this->Filter.filterKey.insert(std::pair<std::string, FilterValue>(key, FilterValue(list)));
		}
	}

	sub = json_geto(js, "sort");
	if (sub) {
		json_t *v;
		std::string list;
		json_array_foreach(sub, v)
			list = list + json_string_value(v) + ",";
		this->Sort.Split(list);
	}

	sub = json_geto(js, "quickFilters");
	if (sub) {
		json_t *v;
		json_array_foreach(sub, v) {
			const char *s = json_string_value(v);
			if (s)
				quickFilters << s;
		}
	}
}

bool KolaMenu::SetQuickFilter(std:: string name)
{
	bool ret = quickFilters.Find(name) || name == "";
	if (ret)
		quickFilter = name;

	return ret;
}

int KolaMenu::GetAlbumCount()
{
	AlbumPage page;
	LowGetPage(&page, 0, 0);
	return albumCount;
}

int KolaMenu::SeekByAlbumId(std::string vid)
{
	prev->Clear();
	cur->Clear();
	next->Clear();
	int count = LowGetPage(cur, "vid", vid, PageSize);

	PageId = cur->pageId;

	if (PageId > 0)
		LowGetPage(prev, PageId - 1, PageSize);
	LowGetPage(next, PageId + 1, PageSize);

	for (int i=0; i<count; i++) {
		KolaAlbum *album = cur->GetAlbum(i);
		if (album && album->vid == vid)
			return i;
	}

	return -1;
}

int KolaMenu::SeekByAlbumName(std::string vid)
{

}

int KolaMenu::Search(AlbumPage &page, std::string keyword, int pageNo)
{

	return 0;
}

int KolaMenu::ParserJson(AlbumPage *page, std::string &text)
{
	int cnt = 0;
	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js) {
		albumCount = json_geti(js, "total", 0);
		page->pageId = json_geti(js, "page", page->pageId);
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

std::string KolaMenu::GetPostData()
{
	int count = 0;
	std::string body("{");
	std::string filter = Filter.GetJsonStr();
	std::string sort = Sort.GetJsonStr();

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
	//std::cout << "Filter Body: " << body << std::endl;

	return body;
}

int KolaMenu::LowGetPage(AlbumPage *page, int pageId, int pageSize)
{
	char url[256];
	std::string text;

	std::string body = GetPostData();

	if (name == "" or cid == -1)
		return 0;

	sprintf(url, "/video/list?page=%d&size=%d&cid=%d", pageId, pageSize, cid);
	if (client->UrlPost(url, body.c_str(), text) == true) {
		page->Clear();
		return ParserJson(page, text);
	}

	return 0;
}

int KolaMenu::LowGetPage(AlbumPage *page, std::string key, std::string value, int pageSize)
{
	char url[256];
	std::string text;

	std::string body = GetPostData();

	if (name == "" or cid == -1)
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

KolaAlbum* KolaMenu::GetAlbum(int position)
{
	int page = position / PageSize;
	if (cur->pageId != page) {
		if (next->pageId == page) {
			AlbumPage *tmp = prev;
			prev = cur;
			cur = next;
			next = tmp;
			next->Clear();
			LowGetPage(next, page + 1, PageSize);
		}
		else if (prev->pageId = page) {
			AlbumPage *tmp = next;
			prev = next;
			cur = prev;
			next = tmp;
			prev->Clear();
			LowGetPage(prev, page - 1, PageSize);
		}
		else {
			prev->Clear();
			cur->Clear();
			next->Clear();
			if (page > 0)
				LowGetPage(prev, page - 1, PageSize);
			LowGetPage(cur, page, PageSize);
			LowGetPage(next, page + 1, PageSize);
		}
	}
	return cur->GetAlbum(position % PageSize);
}

CustomMenu::CustomMenu(std::string fileName) {
	this->fileName = fileName;
	albumIdList.LoadFromFile(fileName);
	albumCount = albumIdList.size();
}

void CustomMenu::AlbumAdd(KolaAlbum *album) {
	if (album)
		AlbumAdd(album->vid);
}

void CustomMenu::AlbumAdd(std::string vid) {
	albumIdList.Add(vid);
	albumCount = albumIdList.size();
}

void CustomMenu::AlbumRemove(KolaAlbum *album) {
	if (album)
		AlbumRemove(album->vid);
}

void CustomMenu::AlbumRemove(std::string vid) {
	albumIdList.Remove(vid);
	albumCount = albumIdList.size();
}

int CustomMenu::GetAlbumCount() {
	albumCount = albumIdList.size();
	return albumCount;
}

bool CustomMenu::SaveToFile(std::string otherFile) {
	if (otherFile != "")
		return albumIdList.SaveToFile(otherFile);
	else
		return albumIdList.SaveToFile(fileName);
}

int CustomMenu::LowGetPage(AlbumPage *page, int pageId, int pageSize)
{
	std::string text;
	int pos = pageId * pageSize;

	text = albumIdList.ToString(pos, pageSize);
	if (text.size() > 0) {
		char buf[128];
		char *pvid;
		std::string url;
		std::string body = GetPostData();

		sprintf(buf, "video/list?page=%d&size=%d&vid=", pageId, pageSize);

		pvid = URLencode(text.c_str());
		text = pvid;
		free(pvid);
		url = buf + text;
		if (client->UrlPost(url, body.c_str(), text) == true) {
			page->Clear();
			return ParserJson(page, text);
		}
	}

	return 0;
}

