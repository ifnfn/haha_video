#include <iostream>

#include "kola.hpp"
#include "json.hpp"

void KolaFilter::KeyAdd(string key, string value)
{
	FilterValue &v = (*this)[key];
	v.Set(value);
}

void KolaFilter::KeyRemove(string key)
{
	filterKey.erase(key);
}

string KolaFilter::GetJsonStr(void)
{
	int count = 0;
	string filter;

	foreach(filterKey, i) {
		string key = i->second.Get();
		if (not key.empty()) {
			filter += "\"" + i->first + "\" : \"" + key + "\", ";
			count++;
		}
	}

	if (count > 0) {
		filter.erase(filter.end() - 2);
		filter += "}";
		filter = "\"filter\" : { " + filter;
	}

	return filter;
}

FilterValue& KolaFilter::operator[] (string key)
{
	map<string, FilterValue>::iterator it = filterKey.find(key);

	if (it == filterKey.end()) {
		filterKey.insert(pair<string, FilterValue>(key, FilterValue()));
		it = filterKey.end();
		it--;
	}

	return it->second;
}

FilterValue::FilterValue(const string items)
{
	Split(items);
}

