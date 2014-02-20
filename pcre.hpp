#ifndef PCRE_HPP
#define PCRE_HPP

#include <pcre.h>
#include <string>
#include <vector>
#include <string.h>

using namespace std;

class KolaPcre {
public:
	KolaPcre();
	~KolaPcre();

	//Add a regrex, pass in name and regrex
	int AddRule(const string &patten);

	//clear all the regrex
	void ClearRules();

	//match all the regrex, also return all the string match to every regrex
	string MatchAll(const char *content);
private:
	vector<pcre*> re_arr;
};

#endif
