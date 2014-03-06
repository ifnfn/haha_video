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

	int AddRule(const string &patten);
	void ClearRules();
	string MatchAll(const char *content);
private:
	vector<pcre*> re_arr;
};

#endif
