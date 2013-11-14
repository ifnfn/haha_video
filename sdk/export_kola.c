extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
LUALIB_API int luaopen_kola(lua_State *L);
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "kola.hpp"
#include "pcre.hpp"

static int f_wget(lua_State *L)
{
	const char *url= lua_tostring(L, 1);
	KolaClient &kola = KolaClient::Instance();
	std::string ret;

	if (kola.UrlGet("", ret, url) == true) {
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

	pcre.AddRule(regular);
	std::string ret = pcre.MatchAll(text);

	lua_pushstring(L, ret.c_str());

	return 1;
}

static const struct luaL_reg wget_lib[] = {
	{"wget", f_wget},
	{"pcre", f_pcre},
	{NULL, NULL},
};

LUALIB_API int luaopen_kola(lua_State *L) {
	luaL_register(L, "kola", wget_lib);
	return 1;
}
