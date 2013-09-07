#ifndef _PCRE_H_
#define _PCRE_H_

#include <pcre.h>
#include <string>
#include <vector>
#include <string.h>

using namespace std;

const int VECSIZE = 300;

class Pcre {
public:
	Pcre();
	~Pcre();

	//Add a regrex, pass in name and regrex
	int AddRule(const string &patten);

	//clear all the regrex
	void ClearRules();

	//match all the regrex, also return all the string match to every regrex
	string MatchAll(const char *content);
private:
	const char *error;
	int erroffset;
	int ovector[VECSIZE];
	vector<pcre*> re_arr;
};
#endif
