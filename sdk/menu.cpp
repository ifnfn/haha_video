#include <iostream>

#include "json.h"
#include "kola.hpp"

KolaMenu::KolaMenu() {
	cid = -1;
	PageId = -1;
	language = "zh";
	//quickFilter = "";
	PageSize = DEFAULT_PAGE_SIZE;
	albumCount = 0;

	client = &KolaClient::Instance();
}

KolaMenu::KolaMenu(json_t *js)
{
	json_t *sub;
	PageSize   = DEFAULT_PAGE_SIZE;
	PageId     = -1;
	albumCount = 0;
	name       = json_gets(js, "name", "");
	cid        = json_geti(js, "cid" , -1);

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

KolaMenu::KolaMenu(const KolaMenu &m)
{
	name         = m.name;
	cid          = m.cid;
	PageSize     = m.PageSize;
	PageId       = m.PageId;
	client       = m.client;
	Filter       = m.Filter;
	Sort         = m.Sort;
	albumCount   = m.albumCount;;
	language     = m.language;
	quickFilter  = m.quickFilter;
	quickFilters = m.quickFilters;
}

bool KolaMenu::SetQuickFilter(std:: string name)
{
	bool ret = quickFilters.Find(name);
	if (ret)
		quickFilter = name;

	return ret;
}

int KolaMenu::GetAlbumCount()
{
	AlbumPage page;
	LowGetPage(page, 0, 0);
	return albumCount;
}

int KolaMenu::Search(AlbumPage &page, std::string keyword, int pageNo)
{

}

int KolaMenu::ParserJson(AlbumPage &page, std::string &text)
{
	int count = 0;
	json_error_t error;
	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js) {
		albumCount = json_geti(js, "total", 0);
		json_t *results = json_geto(js, "result");

		count = ParserJson(page, results);

		json_decref(js);
	}

	return count;
}

int KolaMenu::ParserJson(AlbumPage &page, json_t *js)
{
	int count = 0;

	if (js && json_is_array(js)) {
		json_t *value;
		json_array_foreach(js, value) {
			page.PutAlbum(new KolaAlbum(value));
			count++;
		}
	}

	return count;
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
//	std::cout << "Filter Body: " << body << std::endl;

	return body;
}

int KolaMenu::LowGetPage(AlbumPage &page, int pageId, int pageSize)
{
	char url[256];
	std::string text;

	std::string body = GetPostData();

	if (name == "" or cid == -1)
		return 0;

	sprintf(url, "/video/list?page=%d&size=%d&cid=%d", pageId, pageSize, cid);
	if (client->UrlPost(url, body.c_str(), text) == true) {
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

	return LowGetPage(page, PageId, PageSize);
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

bool CustomMenu::SaveToFile(std::string otherFile) {
	if (otherFile != "")
		return albumIdList.SaveToFile(otherFile);
	else
		return albumIdList.SaveToFile(fileName);
}

int CustomMenu::LowGetPage(AlbumPage &page, int pageId, int pageSize)
{
	int count = 0;
	std::string url = "/video/list?";
	std::string text = "";
	std::string body = GetPostData();
	int pos = pageId * pageSize;
	char buf[128];

	sprintf(buf, "page=%d&size=%d", pageId, pageSize);
	url = url + buf + "&vid=";
	for (; count < pageSize; count++) {
		url = url + albumIdList[pos];
		pos ++;
		if (pos == albumCount)
			break;
		url = url + ",";
	}

	if (count > 0) {
		if (client->UrlPost(url, body.c_str(), text) == true)
			return ParserJson(page, text);
	}

	return 0;
}

