#include <iostream>

#include "kola.hpp"
#include "json.h"


void KolaFilter::KeyAdd(std::string key, std::string value)
{
	(*this)[key].Add(value);
}

void KolaFilter::KeyRemove(std::string key, std::string value)
{
	(*this)[key].Remove(value);
}

std::string KolaFilter::GetJsonStr(void)
{
	int count = 0;
	std::string filter;

	foreach(filterKey, i) {
		int v_count = 0;

		std::string v = i->second.ToString("[", "]", ", ");
		if (v != "") {
			filter += "\"" + i->first + "\":" + v + ",";
			count++;
		}
	}
	if (count > 0) {
		filter.erase(filter.end() - 1);
		filter += "}";
		filter = "\"filter\" : { " + filter;
	}
	std::cout << filter << std::endl;

	return filter;
}

ValueArray& KolaFilter::operator[] (std::string key)
{
	std::map<std::string, ValueArray>::iterator it = filterKey.find(key);

	if (it == filterKey.end()) {
		filterKey.insert(std::pair<std::string, ValueArray>(key, ValueArray()));
		it = filterKey.end();
		it--;
	}

	return it->second;
}
