#include <iostream>

#include "kola.hpp"
#include "json.hpp"

void KolaFilter::KeyAdd(std::string key, std::string value)
{
	FilterValue &v = (*this)[key];
	v.Set(value);
}

void KolaFilter::KeyRemove(std::string key)
{
	filterKey.erase(key);
}

std::string KolaFilter::GetJsonStr(void)
{
	int count = 0;
	std::string filter;

	foreach(filterKey, i) {
		std::string key = i->second.Get();
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

FilterValue& KolaFilter::operator[] (std::string key)
{
	std::map<std::string, FilterValue>::iterator it = filterKey.find(key);

	if (it == filterKey.end()) {
		filterKey.insert(std::pair<std::string, FilterValue>(key, FilterValue()));
		it = filterKey.end();
		it--;
	}

	return it->second;
}

FilterValue::FilterValue(const std::string items)
{
	Split(items);
}

