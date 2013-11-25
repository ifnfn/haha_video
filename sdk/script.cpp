#include <stdio.h>
#include <string.h>
#include <map>
#include <string>

extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
	int luaopen_kola(lua_State *L);
	int luaopen_cjson(lua_State *L);
	int luaopen_LuaXML_lib(lua_State *L);
}

#include "json.h"
#include "kola.hpp"
#include "script.hpp"

char *lua_runscript(lua_State* L, const char *fn, const char *func, int argc, const char **argv)
{
	int i;

	if (luaL_dostring(L, fn)) {
		printf("%s\n%s.\n", fn, lua_tostring(L, -1));
		return NULL;
	}

	lua_getglobal(L, func);

	for (i=0; i < argc; i++)
		lua_pushstring(L, argv[i]);

	// 下面的第二个参数表示带调用的lua函数存在两个参数。
	// 第三个参数表示即使带调用的函数存在多个返回值，那么也只有一个在执行后会被压入栈中。
	// lua_pcall调用后，虚拟栈中的函数参数和函数名均被弹出。
	if (lua_pcall(L, argc, 1, 0)) {
		printf("%s\n%s.\n", fn, lua_tostring(L, -1));
		printf("function ""%s"", parameters: \n", func);
		for (i = 0; i < argc; i++)
			printf("\targv[%d] : %s\n", i, argv[i]);

		return NULL;
	}

	// 此时结果已经被压入栈中。
	if (!lua_isstring(L, -1)) {
		printf("function '%s' must return a string.\n", func);
		lua_pop(L, -1);
		return NULL;
	}

	const char *ret = lua_tostring(L, -1);
	if (ret)
		ret = strdup(ret);

	lua_pop(L, -1);

	return (char*)ret;
}

static const luaL_Reg lualibs[] = {
	{""             , luaopen_base      },
	{LUA_TABLIBNAME , luaopen_table     },
	{LUA_IOLIBNAME  , luaopen_io        },
	{LUA_OSLIBNAME  , luaopen_os        },
	{LUA_STRLIBNAME , luaopen_string    },
	{LUA_MATHLIBNAME, luaopen_math      },
	{LUA_DBLIBNAME  , luaopen_debug     },
	{"kola"         , luaopen_kola      },
	{"cjson"        , luaopen_cjson     },
	{"xml"          , luaopen_LuaXML_lib},
	{NULL, NULL}
};


static void luaL_openmini(lua_State *L)
{
	const luaL_Reg *lib = lualibs;

	for (; lib->func; lib++) {
		lua_pushcfunction(L, lib->func);
		lua_pushstring(L, lib->name);
		lua_call(L, 1, 0);
	}
}

LuaScript::LuaScript()
{
	L = luaL_newstate();
	luaL_openmini(L);
}

LuaScript& LuaScript::Instance()
{
	static LuaScript _lua;

	return _lua;
}

LuaScript::~LuaScript()
{
	lua_close(L);
}

std::string LuaScript::RunScript(int argc, const char **argv, const char *name, const char *fname)
{
	std::string text, ret("");

	if ( GetScript(name, text)) {
		char *r = lua_runscript(L, text.c_str(), fname, argc, argv);
		if (r) {
			ret = r;

			free(r);
		}
	}

	return ret;
}

bool LuaScript::GetScript(const char *name, std::string &text) {
	std::map<std::string ,script>::iterator it = scripts.find(name);
	if (it != scripts.end()) {
		time_t now = time(NULL);
		if (now - it->second.dtime > 60)
			scripts.erase(it);
		else {
			text = it->second.text;
			return true;
		}
	}
	KolaClient &kola = KolaClient::Instance();

	std::string url("/scripts/");

	if (kola.UrlGet(url + name + ".lua", text) == true) {
		scripts.insert(std::pair<std::string, script>(name, script(text)));
		return true;
	}

	return false;
}

ScriptCommand::ScriptCommand() {
	func_name = "kola_main";
	argv = NULL;
	argc = 0;
}
ScriptCommand::~ScriptCommand() {
	for (int i = 0; i < argc; i++)
		free(argv[i]);

	free(argv);
}

bool ScriptCommand::LoadFromJson(json_t *js) {
	script_name = json_gets(js, "script", "");
	json_t *params = json_geto(js, "parameters");
	func_name = json_gets(js, "func_name", "kola_main");
	if (params) {
		argc = json_array_size(params);
		argv = (char **)malloc(sizeof(void*) * argc);
		for (int i = 0; i < argc; i++) {
			json_t *value = json_array_get(params, i);
			argv[i] = strdup(json_string_value(value));
		}
	}

	return script_name != "";
}

std::string ScriptCommand::Run() {
	LuaScript& lua = LuaScript::Instance();
	return lua.RunScript(argc, (const char **)argv, script_name.c_str(), func_name.c_str());
}

