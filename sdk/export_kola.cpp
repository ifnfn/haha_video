extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
LUALIB_API int luaopen_kola(lua_State *L);
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include <math.h>

#include "kola.hpp"
#include "pcre.hpp"
#include "httplib.h"

class WgetTask: public Task {
	public:
		WgetTask(std::string url) {
			this->Url = url;
		}
		void Run() {
			KolaClient &kola = KolaClient::Instance();

			if (kola.UrlGet("", text, Url.c_str()) == false)
				text = "";
		}
		std::string text;
	private:
		std::string Url;
};

static int f_mwget(lua_State *L)
{
	int argc = lua_gettop(L);
	double k;
	const char *v = NULL;
	std::vector<WgetTask> taskList;

	lua_pushnil(L);
	/* table, startkey */
	while (lua_next(L, 1) != 0) {
		/* table, key, value */
		if (lua_type(L, -2) == LUA_TNUMBER && (k = lua_tonumber(L, -2))) {
			if (lua_type(L, -1) == LUA_TSTRING && (v = lua_tostring(L, -1))) {
				taskList.push_back(WgetTask(v));
			}
		}
		lua_pop(L, 1);
	}

	for (size_t i = 0; i < taskList.size(); i++) {
		WgetTask *t = &taskList[i];
		t->Start();
	}

	lua_newtable(L);

	for (size_t i = 0; i < taskList.size(); i++) {
		WgetTask *t = &taskList[i];
		t->Wait();
		lua_pushinteger(L, i + 1);
		lua_pushstring(L, t->text.c_str());
		lua_settable(L, -3);
	}

	return 1;
}

static int f_wget(lua_State *L)
{
	int argc = lua_gettop(L);
	const char *url;
	const char *referer = NULL;
	bool location = true;
	int rc;
	std::vector<std::string> urlList;

	if (lua_type(L, 1) == LUA_TSTRING && (url = lua_tostring(L, 1))) {
		urlList.push_back(url);
	}
	else if (lua_type(L, 1) == LUA_TTABLE) {
		lua_pushnil(L);
		while (lua_next(L, 1) != 0) {
			if (lua_type(L, -1) == LUA_TSTRING && (url = lua_tostring(L, -1))) {
				urlList.push_back(url);
			}

			lua_pop(L, 1);
		}
	}

	if (urlList.size()  == 0)
		return 0;

	if (argc >= 2)
		referer = lua_tostring(L, 2);

	if (argc >= 3)
		location = lua_toboolean(L, 3);

	KolaClient &kola = KolaClient::Instance();
	for (int i = 0; i < urlList.size(); i++) {
		std::string text;
		if (kola.UrlGet("", text, urlList[i].c_str()) == true)
			lua_pushstring(L, text.c_str());
		else
			lua_pushstring(L, "");
	}

	return 1;
}

/**
 * wpost(url, data, referer)
 */

static int f_wpost(lua_State *L)
{
	std::string ret;
	int argc = lua_gettop(L);

	if (argc < 2)
		return 0;

	const char *url = lua_tostring(L, 1);
	const char *data = lua_tostring(L, 2);
	const char *referer = NULL;

	if (argc >= 3)
		referer = lua_tostring(L, 3);

	KolaClient &kola = KolaClient::Instance();

	if (kola.UrlPost("", data, ret, url, referer) == true) {
		lua_pushstring(L, ret.c_str());

		return 1;
	}

	return 0;
}

static int f_pcre(lua_State *L)
{
	const char *regular = lua_tostring(L, 1);
	const char *text = lua_tostring(L, 2);
	Pcre pcre;

	if (text == NULL)
		return 0;
	if (regular == NULL) {
		lua_pushstring(L, text);
		return 1;
	}

	pcre.AddRule(regular);
	std::string ret = pcre.MatchAll(text);

	lua_pushstring(L, ret.c_str());

	return 1;
}

static int f_getserver(lua_State *L)
{
	KolaClient &kola = KolaClient::Instance();
	lua_pushstring(L, kola.GetServer().c_str());

	return 1;
}

static int f_urlencode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	txt = URLencode(txt);

	lua_pushstring(L, txt);
	free((void*)txt);

	return 1;
}

static int f_urldecode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	char *x = strdup(txt);
	txt = URLdecode(x);

	lua_pushstring(L, x);
	free(x);

	return 1;
}

static const struct luaL_reg wget_lib[] = {
	{"wget"      , f_wget}      ,
	{"mwget"     , f_mwget}     ,
	{"wpost"     , f_wpost}     ,
	{"pcre"      , f_pcre}      ,
	{"getserver" , f_getserver} ,
	{"urlencode" , f_urlencode} ,
	{"urldecode" , f_urldecode} ,
	{NULL        , NULL}        ,
};

LUALIB_API int luaopen_kola(lua_State *L) {
	luaL_register(L, "kola", wget_lib);
	return 1;
}
