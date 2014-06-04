#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include <math.h>

#include "lua.hpp"
#include "pcre.hpp"
#include "http.hpp"
#include "kola.hpp"
#include "base64.hpp"
#include "resource.hpp"
#include "common.hpp"

extern "C" {LUALIB_API int luaopen_kola(lua_State *L);}

static int lua_mwget(lua_State *L)
{
	double k;
	const char *v = NULL;
	vector<Http*> taskList;
	MultiHttp multi;

	lua_pushnil(L);
	/* table, startkey */
	while (lua_next(L, 1) != 0) {
		/* table, key, value */
		if (lua_type(L, -2) == LUA_TNUMBER && (k = lua_tonumber(L, -2))) {
			if (lua_type(L, -1) == LUA_TSTRING && (v = lua_tostring(L, -1))) {
				Http *http = new Http();
				http->Open(v);
				taskList.push_back(http);
				multi.Add(http);
			}
		}
		lua_pop(L, 1);
	}
	multi.Exec();

	lua_newtable(L);

	for (size_t i = 0; i < taskList.size(); i++) {
		lua_pushinteger(L, i + 1);

		Http *t = taskList[i];
		if (t->msg == CURLMSG_DONE) {
			lua_pushstring(L, t->buffer.mem);
		}
		else
			lua_pushstring(L, "");

		lua_settable(L, -3);

		delete t;
	}

	return 1;
}

static int lua_wget(lua_State *L)
{
	int argc = lua_gettop(L);
	const char *url = NULL;
	bool cached = true;
	if (argc < 1)
		return 0;
	if (argc >= 1 && lua_type(L, 1) == LUA_TSTRING)
		url = lua_tostring(L, 1);

	if (argc >= 2 && lua_type(L, 2) == LUA_TBOOLEAN)
		cached = lua_toboolean(L, 2);

	if (url) {
		if (cached) {
			KolaClient &kola = KolaClient::Instance();

			Resource* res = kola.resManager->GetResource(url);
			res->Wait();
			string text = res->ToString();
			kola.resManager->RemoveResource(res->GetName());

			if (not text.empty()) {
				lua_pushstring(L, text.c_str());
				return 1;
			}
		}
		else {
			Http http;
			const char *text = http.Get(url);
			if (text) {
				lua_pushstring(L, text);
				return 1;
			}
		}
	}

	return 0;
}

static int lua_wpost(lua_State *L)
{
	string ret;
	int argc = lua_gettop(L);

	if (argc < 2)
		return 0;

	const char *url = lua_tostring(L, 1);
	const char *data = lua_tostring(L, 2);

	KolaClient &kola = KolaClient::Instance();

	if (kola.UrlPost(url, data, ret) == true) {
		lua_pushstring(L, ret.c_str());

		return 1;
	}

	return 0;
}

static int lua_pcre(lua_State *L)
{
	const char *regular = lua_tostring(L, 1);
	const char *text = lua_tostring(L, 2);
	KolaPcre pcre;

	if (text == NULL)
		return 0;
	if (regular == NULL) {
		lua_pushstring(L, text);
		return 1;
	}

	pcre.AddRule(regular);
	string ret = pcre.MatchAll(text);

	lua_pushstring(L, ret.c_str());

	return 1;
}

static int lua_geturl(lua_State *L)
{
	string Url;
	int argc = lua_gettop(L);

	for (int i=0; i < argc; i++) {
		if (argc >= 1 && lua_type(L, 1) == LUA_TSTRING)
			Url = UrlLink(Url, lua_tostring(L, 1));
	}

	if (not Url.empty()) {
		Url = KolaClient::Instance().GetFullUrl(Url);

		lua_pushstring(L, Url.c_str());

		return 1;
	}

	return 0;
}

static int lua_gettime(lua_State *L)
{
	lua_pushnumber(L, KolaClient::Instance().GetTime());

	return 1;
}

static int lua_getdate(lua_State *L)
{
	time_t now = KolaClient::Instance().GetTime();

	struct tm *tm_now = gmtime(&now);

	tm_now->tm_sec = tm_now->tm_min = tm_now->tm_hour = 0;
	now = mktime(tm_now);

	lua_pushnumber(L, now);

	return 1;
}

static int lua_urlencode(lua_State *L)
{
	string txt = lua_tostring(L, 1);

	if (not txt.empty()) {
		lua_pushstring(L, UrlEncode(txt).c_str());
		return 1;
	}

	return 0;
}

static int lua_urldecode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);

	if (txt) {
		string text = UrlDecode(txt);
		lua_pushstring(L, text.c_str());
		return 1;
	}

	return 0;
}

static int lua_base64_encode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	if (txt) {
		string ret = base64encode(txt);
		lua_pushstring(L, ret.c_str());

		return 1;
	}

	return 0;
}

static int lua_base64_decode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	if (txt) {
		size_t in_size = strlen(txt);
		size_t out_size = in_size * 3 / 4 + 1;
		unsigned char *out = (unsigned char*)calloc(1, out_size);
		base64decode((const unsigned char*)txt, in_size, out, out_size);
		lua_pushstring(L, (char*)out);
		free(out);
		return 1;
	}

	return 0;
}

static int StringToTime(const string &strDateStr,time_t &timeData)
{
	char *pBeginPos = (char*) strDateStr.c_str();
	char *pPos = strstr(pBeginPos,"-");
	if(pPos == NULL)
	{
		printf("strDateStr[%s] err \n", strDateStr.c_str());
		return -1;
	}
	int iYear = atoi(pBeginPos);
	int iMonth = atoi(pPos + 1);
	pPos = strstr(pPos + 1,"-");
	if(pPos == NULL)
	{
		printf("strDateStr[%s] err \n", strDateStr.c_str());
		return -1;
	}
	int iDay = atoi(pPos + 1);
	int iHour=0;
	int iMin=0;
	int iSec=0;
	pPos = strstr(pPos + 1," ");
	//为了兼容有些没精确到时分秒的
	if(pPos != NULL) {
		iHour=atoi(pPos + 1);
		pPos = strstr(pPos + 1,":");
		if(pPos != NULL) {
			iMin=atoi(pPos + 1);
			pPos = strstr(pPos + 1,":");
			if(pPos != NULL)
				iSec=atoi(pPos + 1);
		}
	}

	struct tm sourcedate;
	bzero((void*)&sourcedate,sizeof(sourcedate));
	sourcedate.tm_sec = iSec;
	sourcedate.tm_min = iMin;
	sourcedate.tm_hour = iHour;
	sourcedate.tm_mday = iDay;
	sourcedate.tm_mon = iMonth - 1;
	sourcedate.tm_year = iYear - 1900;
	timeData = mktime(&sourcedate);

	return 0;
}

static int lua_date(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	if (txt) {
		string text = txt;
		time_t time;
		if (StringToTime(text, time) == 0) {
			lua_pushinteger(L, time);

			return 1;
		}
	}

	return 0;
}

static int lua_md5(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	if (txt) {
		lua_pushstring(L, MD5(txt, strlen(txt)).c_str());

		return 1;
	}

	return 0;
}

static int lua_getchipid(lua_State *L)
{
	lua_pushstring(L, GetChipKey().c_str());
	return 0;
}


static int lua_getserial(lua_State *L)
{
	lua_pushstring(L, GetSerial().c_str());
	return 0;
}

static int lua_strtrim(lua_State *L)
{
	int front = 0, back;
	const char *str = luaL_checklstring(L, 1, (size_t *)(&back));
	const char *del = luaL_optstring(L, 2, "\t\n\r ");
	--back;

	while (front <= back && strchr(del, str[front]))
		++front;
	while (back > front && strchr(del, str[back]))
		--back;

	lua_pushlstring(L, &str[front], back - front + 1);
	return 1;
}

/* strsplit & strjoin adapted from code by Norganna */
static int lua_strsplit(lua_State *L)
{
	const char *sep = luaL_checkstring(L, 1);
	const char *str = luaL_checkstring(L, 2);
	int limit = luaL_optint(L, 3, 0);
	int count = 0;
	/* Set the stack to a predictable size */
	lua_settop(L, 0);
	/* Initialize the result count */
	/* Tokenize the string */
	if(!limit || limit > 1) {
		const char *end = str;
		while(*end) {
			int issep = 0;
			const char *s = sep;
			for(; *s; ++s) {
				if(*s == *end) {
					issep = 1;
					break;
				}
			}
			if(issep) {
				luaL_checkstack(L, count+1, "too many results");
				lua_pushlstring(L, str, (end-str));
				++count;
				str = end+1;
				if(count == (limit-1)) {
					break;
				}
			}
			++end;
		}
	}
	/* Add the remainder */
	luaL_checkstack(L, count+1, "too many results");
	lua_pushstring(L, str);
	++count;
	/* Return with the number of values found */
	return count;
}

static int lua_strjoin(lua_State *L)
{
	size_t seplen;
	int entries;
	const char *sep = luaL_checklstring(L, 1, &seplen);

	/* Guarantee we have 1 stack slot free */
	lua_remove(L, 1);

	entries = lua_gettop(L);

	if (seplen == 0) /* If there's no seperator, then this is the same as a concat */
		lua_concat(L, entries);
	else if (entries == 0) /* If there are no entries then we can't concatenate anything */
		lua_pushstring(L, "");
	else if (entries == 1) /* If there's only one entry, just return it */
		;
	else {
		luaL_Buffer b;
		int i;

		/* Set up buffer to store resulting string */
		luaL_buffinit(L, &b);
		for(i = 1; i <= entries; ++i) {
			/* Push the current entry and add it to the buffer */
			lua_pushvalue(L, i);
			luaL_addvalue(&b);
			/* Add the separator to the buffer */
			if (i < entries) {
				luaL_addlstring(&b, sep, seplen);
			}
		}
		luaL_pushresult(&b);
	}

	return 1;
}

static int lua_area(lua_State *L)
{
	KolaArea area;

	KolaClient &kola = KolaClient::Instance();
	if (kola.GetArea(area)) {
		lua_newtable(L);
		lua_pushstring(L, "ip");
		lua_pushstring(L, area.ip.c_str());
		lua_settable(L, -3);

		lua_pushstring(L, "isp");
		lua_pushstring(L, area.isp.c_str());
		lua_settable(L, -3);

		lua_pushstring(L, "country");
		lua_pushstring(L, area.country.c_str());
		lua_settable(L, -3);

		lua_pushstring(L, "city");
		lua_pushstring(L, area.city.c_str());
		lua_settable(L, -3);

		lua_pushstring(L, "province");
		lua_pushstring(L, area.province.c_str());
		lua_settable(L, -3);

		return 1;
	}

	return 0;
}

static const struct luaL_Reg kola_lib[] = {
	{"base64_encode" , lua_base64_encode },
	{"base64_decode" , lua_base64_decode },
	{"wget"          , lua_wget          },
	{"mwget"         , lua_mwget         },
	{"wpost"         , lua_wpost         },
	{"pcre"          , lua_pcre          },
	{"geturl"        , lua_geturl        },
	{"gettime"       , lua_gettime       },
	{"getdate"       , lua_getdate       },
	{"urlencode"     , lua_urlencode     },
	{"urldecode"     , lua_urldecode     },
	{"md5"           , lua_md5           },
	{"date"          , lua_date          },
	{"chipid"        , lua_getchipid     },
	{"serial"        , lua_getserial     },
	{"strtrim"       , lua_strtrim       },
	{"strsplit"      , lua_strsplit      },
	{"strjoin"       , lua_strjoin       },
	{"getarea"       , lua_area          },

	{NULL            , NULL},
};

LUALIB_API int luaopen_kola(lua_State *L) {
	luaL_newlib(L, kola_lib);
	return 1;
}

