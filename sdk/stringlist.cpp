#include <iostream>
#include <fstream>
#include <string.h>

#include "kola.hpp"

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


void StringList::Add(std::string v)
{
	StringList::iterator iter = find(begin(), end(), v);
	if (iter == end())
		push_back(v);
}

void StringList::Remove(std::string v)
{
	StringList::iterator iter = find(begin(), end(), v);
	if (iter != end())
		erase(iter);
}

void StringList::operator<< (std::string v)
{
	Add(v);
}

void StringList::operator>> (std::string v)
{
	Remove(v);
}

bool StringList::Find(std::string v)
{
	StringList::iterator iter = find(begin(), end(), v);

	return iter != end();
}

std::string StringList::ToString(int offset, int len, std::string s, std::string e, std::string split)
{
	std::string ret;
	int count = size();

	if (offset + len > count)
		count = count - offset;
	else
		count = len;

	if (count > 0) {
		ret = s;
		for (int i = 0; i < count - 1; i++)
			ret += at(i + offset) + split;

		if (count > 0)
			ret += at(count - 1) + e;
	}

	return ret;
}

std::string StringList::ToString(std::string s, std::string e, std::string split)
{
	return ToString(0, size(), s, e, split);
}

void StringList::Split(const std::string items, std::string sp)
{
	clear();
	split(items, sp, this);
}

bool StringList::SaveToFile(std::string fileName)
{
	FILE *fp = fopen(fileName.c_str(), "w");
	if (fp) {
		for (int i = 0; i < size(); i++) {
			const char *p = at(i).c_str();
			fprintf(fp, "%s\n", p);
		}
		fclose(fp);

		return true;
	}

	return false;
}

bool StringList::LoadFromFile(std::string fileName)
{
	FILE *fp = fopen(fileName.c_str(), "r");

	if (fp) {
		char buffer[1024];
		while (!feof(fp)) {
			char *p = fgets(buffer, 1023, fp);
			if (p) {
				int len = strlen(p);
				if (p[len - 1] == '\n')
					p[len - 1] = 0;
				push_back(p);
			}
		}
		fclose(fp);

		return true;
	}

	return false;
}

