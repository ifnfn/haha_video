#ifndef _PCRE_H_
#define _PCRE_H_

#include <pcre.h>
#include <string>
#include <vector>
#include <string.h>

class Pcre {
	public:
		Pcre();
		~Pcre();

		//Add a regrex, pass in name and regrex
		int AddRule(const std::string &patten);

		//clear all the regrex
		void ClearRules();

		//match all the regrex, also return all the string match to every regrex
		std::string MatchAll(const char *content);
	private:
		std::vector<pcre*> re_arr;
};
#endif
