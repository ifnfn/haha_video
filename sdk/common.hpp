#ifndef __kolatv__common__
#define __kolatv__common__

#include "kola.hpp"

extern string UrlEncode(const string& url);
extern string UrlDecode(const string& sIn);
extern string GetChipKey(void);
extern string GetSerial(void);
extern string MD5(const char *data, size_t size);
extern string GetIP(const char *hostp);
extern void   Split(const string& src, const string& separator, vector<string>& dest);
extern string stringlink(string key, string value);
extern string UrlLink(string a, string b);

#endif /* defined(__kolatv__common__) */
