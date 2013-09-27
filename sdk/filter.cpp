#include <iostream>

#include "kola.hpp"
#include "json.h"

void split(const std::string &s, std::string delim, std::vector< std::string > *ret)
{
	size_t last = 0;
	size_t index=s.find_first_of(delim, last);

	while (index!=std::string::npos) {
		ret->push_back(s.substr(last,index-last));
		last = index + 1;
		index=s.find_first_of(delim, last);
	}
	if (index - last > 0)
		ret->push_back(s.substr(last,index-last));
}

void KolaFilter::KeyAdd(std::string key, std::string value)
{
	FilterValue &v = (*this)[key];
	v.Set(value);
}

void KolaFilter::KeyRemove(std::string key, std::string value)
{
	filterKey.erase(key);
}

std::string KolaFilter::GetJsonStr(void)
{
	int count = 0;
	std::string filter;

	foreach(filterKey, i) {
		if (i->second.Get() != "") {
			filter += "\"" + i->first + "\" : \"" + i->second.Get() + "\", ";
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

void KolaFilter::LoadFromJson(json_t *js)
{

}

FilterValue::FilterValue(const std::string items)
{
	split(items, ",", this);
}
#if 0
ValueArray::ValueArray(const std::string items)
{
	split(items, ",", this);
}

void ValueArray::LoadValue(const std::string items)
{
	split(items, ",", this);
}

#endif
