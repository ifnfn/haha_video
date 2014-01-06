#include <stdio.h>

#include <iostream>
#include "pcre.hpp"

#define VECSIZE 300
using namespace std;

Pcre::Pcre()
{
	re_arr.clear();
}

Pcre::~Pcre()
{
	for(size_t i=0; i<re_arr.size(); i++)
		pcre_free(re_arr[i]);
}

//Add a regrex patten and compile it.
int Pcre::AddRule(const string &patten)
{
	const char *error;
	int erroffset;
	pcre *re = pcre_compile(
			patten.c_str(), /* the pattern                  */
			0,              /* default options              */
			&error,         /* for error message            */
			&erroffset,     /* for error offset             */
			NULL);          /* use default character tables */

	if(re == NULL) {
		printf("pcre compile failed, offset %d: %s\n", erroffset, error);
		return -1;
	}
	else {
		re_arr.push_back(re);
	}

	return 0;
}

//clear all the rule
void Pcre::ClearRules()
{
	for(size_t i=0; i<re_arr.size(); i++)
		pcre_free(re_arr[i]);

	re_arr.clear();
}

//match all regrex, if any match, return the matched patten name and it's values
string Pcre::MatchAll(const char *content)
{
	int length = (int)strlen(content);
	string result("");
	int ovector[VECSIZE] ={'\0'};

	for(size_t i=0; i<re_arr.size(); i++) {
		int offset = 0;
		int rc;

		while(offset < length && (rc = pcre_exec(re_arr[i], NULL, content, length, offset, PCRE_NOTEMPTY, ovector, VECSIZE)) >= 0) {
			//			printf("rc=%d\n", rc);
			result.append(content, ovector[2], ovector[3] - ovector[2]);
			result = result + "\n";

			offset = ovector[2 * rc - 1];
			//offset = ovector[1];
			//flags |= PCRE_NOTBOL;
		}
	}
	//cout << result << endl;
	return result;
}

