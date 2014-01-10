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

extern "C" {LUALIB_API int luaopen_kola(lua_State *L);}

static int f_mwget(lua_State *L)
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
				Http *http = new Http(v);
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

static int f_wget(lua_State *L)
{
	int argc = lua_gettop(L);
	const char *url;
	if (argc < 1)
		return 0;

	if (lua_type(L, 1) == LUA_TSTRING && (url = lua_tostring(L, 1))) {
		KolaClient &kola = KolaClient::Instance();
		
		Resource* res = kola.resManager->GetResource(url);
		res->score = 254; // 优先级低于过期图片
		res->Wait();
		lua_pushstring(L, res->ToString().c_str());
		res->DecRefCount();
	}

	return 1;
}

static int f_wpost(lua_State *L)
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

static int f_pcre(lua_State *L)
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

static int f_getserver(lua_State *L)
{
	lua_pushstring(L, KolaClient::Instance().GetServer().c_str());

	return 1;
}

static int f_gettime(lua_State *L)
{
	lua_pushnumber(L, KolaClient::Instance().GetTime());

	return 1;
}

static int f_urlencode(lua_State *L)
{
	string txt = lua_tostring(L, 1);

	if (not txt.empty()) {
		lua_pushstring(L, UrlEncode(txt).c_str());
		return 1;
	}

	return 0;
}

static int f_urldecode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);

	if (txt) {
		string text = UrlDecode(txt);
		lua_pushstring(L, text.c_str());
		return 1;
	}

	return 0;
}

static int f_base64_encode(lua_State *L)
{
	const char *txt = lua_tostring(L, 1);
	if (txt) {
		string ret = base64encode(txt);
		lua_pushstring(L, ret.c_str());

		return 1;
	}

	return 0;
}

static int f_base64_decode(lua_State *L)
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

static const struct luaL_Reg kola_lib[] = {
	{"base64_encode" , f_base64_encode},
	{"base64_decode" , f_base64_decode},
	{"wget"          , f_wget},
	{"mwget"         , f_mwget},
	{"wpost"         , f_wpost},
	{"pcre"          , f_pcre},
	{"getserver"     , f_getserver},
	{"gettime"       , f_gettime},
	{"urlencode"     , f_urlencode},
	{"urldecode"     , f_urldecode},
	{NULL            , NULL},
};

LUALIB_API int luaopen_kola(lua_State *L) {
	luaL_newlib(L, kola_lib);
	return 1;
}

