#include <stdio.h>
#include <string.h>
#include <map>
#include <string>
#include <iostream>

extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
	int luaopen_kola(lua_State *L);
	int luaopen_cjson(lua_State *L);
	int luaopen_LuaXML_lib(lua_State *L);
	int luaopen_cURL(lua_State* L);
}

#include "json.hpp"
#include "kola.hpp"
#include "script.hpp"

static std::string lua_runscript(lua_State* L, const char *fn, const char *func, int argc, const char **argv)
{
	int i;

	std::string ret;

	if (luaL_dostring(L, fn)) {
		printf("%s\n%s.\n", fn, lua_tostring(L, -1));
		return ret;
	}

	lua_getglobal(L, func);

	for (i=0; i < argc; i++) {
		if (argv[i] == NULL)
			printf("argc[%d] error\n", i);
		else
			lua_pushstring(L, argv[i]);
	}

	// 下面的第二个参数表示带调用的lua函数存在两个参数。
	// 第三个参数表示即使带调用的函数存在多个返回值，那么也只有一个在执行后会被压入栈中。
	// lua_pcall调用后，虚拟栈中的函数参数和函数名均被弹出。
	if (lua_pcall(L, argc, 1, 0)) {
		printf("%s.\n", lua_tostring(L, -1));
		printf("%s(", func);
		for (i = 0; i < argc - 1; i++)
			printf("\"%s\", ", argv[i]);

		if (argc > 0)
			printf("\"%s\")\n", argv[argc - 1]);

		return ret;
	}

	// 此时结果已经被压入栈中。
	if (!lua_isstring(L, -1)) {
		printf("[Warning] function '%s' must return a string.\n", func);
		lua_pop(L, -1);
		return ret;
	}


	const char *r = lua_tostring(L, -1);

	if (r)
		ret.assign(r);

	lua_pop(L, -1);

	return ret;
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
	//{"cURL"         , luaopen_cURL      },

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
	std::string text, ret;

	if ( GetScript(name, text))
		ret = lua_runscript(L, text.c_str(), fname, argc, argv);

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

ScriptCommand::ScriptCommand(json_t *js)
{
	func_name = "kola_main";
	argv = NULL;
	argc = 0;

	if (js)
		LoadFromJson(js);
}

ScriptCommand::~ScriptCommand()
{
	for (int i = 0; i < argc; i++) {
		if (argv[i])
			free(argv[i]);
	}

	free(argv);
}

bool ScriptCommand::LoadFromJson(json_t *js) {
	json_gets(js, "script", script_name); 
	json_gets(js, "function", func_name);
	json_t *params = json_geto(js, "parameters");

	if (params) {
		argc = json_array_size(params);
		argv = (char **)calloc(sizeof(void*), argc);
		for (int i = 0; i < argc; i++) {
			json_t *value = json_array_get(params, i);

			if (json_is_string(value))
				argv[i] = strdup(json_string_value(value));
			else if (json_is_integer(value)) {
				char buf[128];
				sprintf(buf, "%d", json_integer_value(value));

				argv[i] = strdup(buf);
			}
			else if (json_is_number(value)) {
				char buf[128];
				sprintf(buf, "%f", json_integer_value(value));

				argv[i] = strdup(buf);
			}
		}
	}

	return script_name != "";
}

std::string ScriptCommand::Run()
{
	std::string ret;
	if (Exists()) {
		LuaScript& lua = LuaScript::Instance();
		ret = lua.RunScript(argc, (const char **)argv, script_name.c_str(), func_name.c_str());
	}

	return ret;
}

