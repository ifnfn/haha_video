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
#include "httplib.h"

static int f_wget(lua_State *L)
{
	int argc = lua_gettop(L);
	const char *url= lua_tostring(L, 1);
	const char *referer = NULL;
	bool location = true;
	int rc;

	if (argc >= 2)
		referer = lua_tostring(L, 2);

	if (argc >= 3)
		location = lua_toboolean(L, 3);

	http_client_t *http_client;
	http_resp_t *http_resp = NULL;

	http_client = http_init_connection(url);
	if (http_client == NULL) {
		printf("%s error: %s\n", __func__, url);
		return 0;
	}
	http_set_location(http_client, 0);
	rc = http_get(http_client, "", &http_resp, NULL, referer);
	if (rc > 0 && http_resp && (http_resp)->body) {
		const char * ret = http_resp->body;
		lua_pushstring(L, ret);
		rc =  1;
	}
	else
		rc = 0;

	http_free_connection(http_client);
	http_resp_free(http_resp);

	return rc;
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

static const struct luaL_reg wget_lib[] = {
	{"wget", f_wget},
	{"pcre", f_pcre},
	{NULL, NULL},
};

LUALIB_API int luaopen_kola(lua_State *L) {
	luaL_register(L, "kola", wget_lib);
	return 1;
}
