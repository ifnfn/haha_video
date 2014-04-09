#include <iostream>
#include <unistd.h>
#include <time.h>

#include "kola.hpp"
#include "json.hpp"
#include "base64.hpp"
#include "threadpool.hpp"

bool VideoResolution::Empty()
{
	return urls.empty();
}

void VideoResolution::Clear()
{
	urls.clear();
}

void VideoResolution::Calc()
{
	json_error_t error;
	const char *key;
	json_t *value;
	string text = GetString();

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
	if (js == NULL) {
		printf("Json error: %s, line: %d, colun: %d, position: %d, error: %s\n",
		       text.c_str(),
		       error.line,
		       error.column,
		       error.position,
		       error.text);
		return;
	}

	json_object_foreach(js, key, value) {
		if (json_geti(value, "default", 0) == 1) {
			defaultKey = key;
		}
		urls.insert(pair<string, Variant>(key, Variant(value)));
	}

	json_delete(js);
}

void VideoResolution::GetResolution(StringList& res)
{
	if (Empty())
		Calc();

	for (map<string, Variant>::iterator it = urls.begin(); it != urls.end(); it++) {
		res.Add(it->first);
	}
}

void VideoResolution::SetResolution(string &res)
{
	this->defaultKey = res;
}

bool VideoResolution::GetVariant(string &key, Variant &var)
{
	if (key.empty())
		key = defaultKey;
	map<string ,Variant>::iterator it = urls.find(key);
	if (it != urls.end()) {
		var = it->second;
		return true;
	}

	return false;
}

string VideoResolution::GetVideoUrl()
{
	string url;
	string key;
	bool find;

	if (Empty())
		Calc();

	key = vid + defaultKey;

	UrlCache &cache = KolaClient::Instance().cache;

	find = cache.FindByVid(key, url);

	if (find) {
		return url;
	}

	if (not Empty()) {
		map<string ,Variant>::iterator it = urls.find(defaultKey);
		if (it != urls.end()) {
			url = it->second.GetString();
		}
		else {
			it = urls.begin();
			url = it->second.GetString();
		}
		cache.Set(key, url);

		return url;
	}

	return "";
}
