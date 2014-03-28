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
			res->DecRefCount();
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

static int lua_getserver(lua_State *L)
{
	lua_pushstring(L, KolaClient::Instance().GetServer().c_str());

	return 1;
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

static const struct luaL_Reg kola_lib[] = {
	{"base64_encode" , lua_base64_encode},
	{"base64_decode" , lua_base64_decode},
	{"wget"          , lua_wget},
	{"mwget"         , lua_mwget},
	{"wpost"         , lua_wpost},
	{"pcre"          , lua_pcre},
	{"geturl"        , lua_geturl},
	{"getserver"     , lua_getserver},
	{"gettime"       , lua_gettime},
	{"getdate"       , lua_getdate},
	{"urlencode"     , lua_urlencode},
	{"urldecode"     , lua_urldecode},
	{"md5"           , lua_md5},
	{"date"          , lua_date},
	{"chipid"        , lua_getchipid},
	{"serial"        , lua_getserial},

	{NULL            , NULL},
};

LUALIB_API int luaopen_kola(lua_State *L) {
	luaL_newlib(L, kola_lib);
	return 1;
}

