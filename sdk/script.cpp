#include <stdio.h>
#include <string.h>
#include <map>
#include <string>
#include <iostream>
#include <lua.hpp>

extern "C" {
	int luaopen_kola(lua_State *L);
	int luaopen_cjson(lua_State *L);
	int luaopen_LuaXML_lib(lua_State *L);
	int luaopen_cURL(lua_State* L);
}

#include "json.hpp"
#include "kola.hpp"
#include "script.hpp"

static string lua_runscript(lua_State* L, const char *fn, const char *func, int argc, const char **argv)
{
	int i;

	string ret;

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

	// 下面的第二个参数表示带调用的lua函数存在argc个参数。
	// 第三个参数表示即使带调用的函数存在多个返回值，那么也只有一个在执行后会被压入栈中。
	// lua_pcall调用后，虚拟栈中的函数参数和函数名均被弹出。
	if (lua_pcall(L, argc, 1, 1)) {
#if TEST
		printf("%s.\n", lua_tostring(L, -1));
		printf("%s(", func);
		for (i = 0; i < argc - 1; i++)
			printf("\"%s\", ", argv[i]);

		if (argc > 0)
			printf("\"%s\")\n", argv[argc - 1]);
#endif

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
	{"_G"           , luaopen_base},
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
	//{LUA_LOADLIBNAME, luaopen_package},
	//{LUA_COLIBNAME, luaopen_coroutine},
	//{LUA_BITLIBNAME, luaopen_bit32},

	{NULL, NULL}
};

static void luaL_openmini(lua_State *L)
{
	const luaL_Reg *lib;
	for (lib = lualibs; lib->func; lib++) {
		luaL_requiref(L, lib->name, lib->func, 1);
		lua_pop(L, 1);  /* remove lib */
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

string LuaScript::RunScript(int argc, const char **argv, const char *name, const char *fname)
{
	string code, ret;

	if ( GetScript(name, code)) {
		int top = lua_gettop(L);
		ret = lua_runscript(L, code.c_str(), fname, argc, argv);
		lua_settop(L, top);
	}

	return ret;
}

bool LuaScript::GetScript(const char *name, string &text)
{
	map<string ,script>::iterator it = scripts.find(name);
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

	string url("/scripts/");

	if (kola.UrlGet(url + name + ".lua", text) == true) {
		scripts.insert(pair<string, script>(name, script(text)));
		return true;
	}

	return false;
}

enum {
	SC_NONE=0,
	SC_SCRIPT=1,
	SC_STRING=2,
	SC_INTEGER=3,
	SC_DOUBLE=4
};

ScriptCommand::ScriptCommand(json_t *js)
{
	func_name = "kola_main";
	argv = NULL;
	argc = 0;
	directText = false;

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

void ScriptCommand::AddParams(int arg)
{
	char buffer[64];

	sprintf(buffer, "%d", arg);

	AddParams(buffer);
}

void ScriptCommand::AddParams(const char *arg)
{
	argc++;
	size_t size = sizeof(void*) * argc;

	if (argv)
		argv = (char**)realloc(argv, size);
	else
		argv = (char**)malloc(size);

	argv[argc - 1] = strdup(arg);
}

bool ScriptCommand::LoadFromJson(json_t *js)
{
	bool ret;

	// 直接值
	json_t *tx = json_geto(js ,"text");
	if (tx != NULL) {
		text = json_string_value(tx);

		directText = true;
		return true;
	}

	json_gets(js, "script", script_name);
	ret = script_name.empty();

	if (ret)
		return false;
	json_gets(js, "function", func_name);
	json_t *params = json_geto(js, "parameters");

	if (params) {
		int count = json_array_size(params);
		for (int i = 0; i < count; i++) {
			json_t *value = json_array_get(params, i);

			if (json_is_string(value))
				AddParams(json_string_value(value));
			else if (json_is_integer(value)) {
				char buf[128];
				sprintf(buf, "%d", json_integer_value(value));

				AddParams(buf);
			}
			else if (json_is_number(value)) {
				char buf[128];
				sprintf(buf, "%f", json_real_value(value));

				AddParams(buf);
			}
		}
	}

	return true;
}

string ScriptCommand::Run()
{
	if (directText)
		return text;

	string ret;
	if (Exists()) {
		LuaScript& lua = LuaScript::Instance();
		ret = lua.RunScript(argc, (const char **)argv, script_name.c_str(), func_name.c_str());
	}

	return ret;
}

bool Variant::LoadFromJson(json_t *js)
{
	if (json_is_string(js)) {
		directValue = SC_STRING;
		valueStr = json_string_value(js);

		return true;
	}
	else if (json_is_integer(js)) {
		directValue = SC_INTEGER;
		valueInt = json_integer_value(js);

		return true;
	}
	else if (json_is_real(js)) {
		directValue = SC_DOUBLE;
		valueDouble = json_real_value(js);

		return true;
	}

	else if (json_is_object(js)) {
		if (ScriptCommand::LoadFromJson(js)) {
			directValue = SC_SCRIPT;

			return true;
		}
	}

	directValue = SC_STRING;
	json_dump_str(js, valueStr);

	return false;
}

Variant::Variant(json_t *js) : ScriptCommand()
{
	directValue = SC_NONE;
	LoadFromJson(js);
}

string Variant::GetString()
{
	if (directValue == SC_DOUBLE) {
		char buffer[128];
		sprintf(buffer, "%f", valueDouble);

		return buffer;
	}
	else if (directValue == SC_STRING) {
		return valueStr;
	}
	else if (directValue == SC_INTEGER) {
		char buffer[32];
		sprintf(buffer, "%ld", valueInt);

		return buffer;
	}
	else if (directValue == SC_SCRIPT) {
		return Run();
	}

	return "";
}

long Variant::GetInteger()
{
	if (directValue == SC_DOUBLE) {
		return int(valueDouble);
	}
	else if (directValue == SC_STRING) {
		try {
			return atoi(valueStr.c_str());
		}
		catch(exception &ex) {
			return 0;
		}
	}
	else if (directValue == SC_INTEGER) {
		return valueInt;
	}
	else if (directValue == SC_SCRIPT) {
		string text = Run();
		try {
			return atoi(text.c_str());
		}
		catch(exception &ex) {
			return 0;
		}

	}

	return 0;
}

double Variant::GetDouble()
{
	if (directValue == SC_DOUBLE) {
		return valueDouble;
	}
	else if (directValue == SC_INTEGER) {
		return valueInt;
	}
	else if (directValue == SC_STRING) {
		try {
			return atof(valueStr.c_str());
		}
		catch(exception &ex) {
			return 0.0;
		}
	}
	else if (directValue == SC_SCRIPT) {
		string text = Run();
		try {
			return atof(text.c_str());
		}
		catch(exception &ex) {
			return 0.0;
		}

	}

	return 0.0;
}
