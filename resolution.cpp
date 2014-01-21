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

void VideoResolution::Set()
{
	json_error_t error;
	const char *key;
	json_t *value;
	string text = GetString();

	json_t *js = json_loads(text.c_str(), JSON_DECODE_ANY, &error);
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
		Set();
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
	if (Empty())
		Set();

	if (not Empty()) {
		map<string ,Variant>::iterator it = urls.find(defaultKey);
		if (it != urls.end()) {
			return it->second.GetString();
		}
		else {
			it = urls.begin();
			return it->second.GetString();
		}
	}

	return "";
}
