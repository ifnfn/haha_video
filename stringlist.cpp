#include <iostream>
#include <fstream>
#include <string.h>

#include "kola.hpp"

void split(const string& src, const string& separator, vector<string>& dest)
{
	string str = src;
	string substring;
	string::size_type start = 0, index;

	do {
		index = str.find_first_of(separator,start);
		if (index != string::npos) {
			substring = str.substr(start,index-start);
			dest.push_back(substring);
			start = str.find_first_not_of(separator,index);
			if (start == string::npos) return;
		}
	}while(index != string::npos);

	//the last token
	substring = str.substr(start);
	dest.push_back(substring);
}

void StringList::Add(string v)
{
	StringList::iterator iter = find(begin(), end(), v);
	if (iter == end())
		push_back(v);
}

void StringList::Remove(string v)
{
	StringList::iterator iter = find(begin(), end(), v);
	if (iter != end())
		erase(iter);
}

void StringList::operator<< (string v)
{
	Add(v);
}

void StringList::operator>> (string v)
{
	Remove(v);
}

bool StringList::Find(string v)
{
	StringList::iterator iter = find(begin(), end(), v);

	return iter != end();
}

string StringList::ToString(size_t offset, size_t len, string s, string e, string split)
{
	string ret;
	size_t count = size();

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

string StringList::ToString(string s, string e, string split)
{
	return ToString(0, (int)size(), s, e, split);
}

void StringList::Split(const string items, string sp)
{
	clear();
	split(items, sp, *this);
}

bool StringList::SaveToFile(string fileName)
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

bool StringList::LoadFromFile(string fileName)
{
	FILE *fp = fopen(fileName.c_str(), "r");

	if (fp) {
		char buffer[1024];
		while (!feof(fp)) {
			char *p = fgets(buffer, 1023, fp);
			if (p) {
				size_t len = strlen(p);
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

