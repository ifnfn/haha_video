#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <map>
#include <string>
#include <iostream>
#include <lua.hpp>
#include <signal.h>
#define __USE_GNU
#include <unistd.h>
#ifdef LINUX
#include <crypt.h>
#endif

//#include <openssl/aes.h>

extern "C" {
	LUALIB_API int luaopen_kola(lua_State *L);
	LUALIB_API int luaopen_cjson(lua_State *L);
	LUALIB_API int luaopen_LuaXML_lib(lua_State *L);
	LUALIB_API int luaopen_cURL(lua_State* L);
}

#include "json.hpp"
#include "kola.hpp"
#include "script.hpp"


static lua_State *globalL = NULL;

static void lstop (lua_State *L, lua_Debug *ar)
{
	(void)ar;  /* unused arg. */
	lua_sethook(L, NULL, 0, 0);
	luaL_error(L, "interrupted!");
}

static void laction (int i)
{
	signal(i, SIG_DFL); /* if another SIGINT happens before lstop,
			       terminate process (default action) */
	lua_sethook(globalL, lstop, LUA_MASKCALL | LUA_MASKRET | LUA_MASKCOUNT, 1);
}

static int traceback (lua_State *L)
{
	const char *msg = lua_tostring(L, 1);
	if (msg)
		luaL_traceback(L, L, msg, 1);
	else if (!lua_isnoneornil(L, 1)) {               /* is there an error object?     */
		if (!luaL_callmeta(L, 1, "__tostring"))  /* try its 'tostring' metamethod */
			lua_pushliteral(L, "(no error message)");
	}
	return 1;
}

static int docall (lua_State *L, int narg, int nres)
{
	int status;
	int base = lua_gettop(L) - narg;  /* function index               */
	lua_pushcfunction(L, traceback);  /* push traceback function      */
	lua_insert(L, base);              /* put it under chunk and args  */
	globalL = L;                      /* to be available to 'laction' */
	signal(SIGINT, laction);
	status = lua_pcall(L, narg, nres, base);
	signal(SIGINT, SIG_DFL);
	lua_remove(L, base);              /* remove traceback function    */
	return status;
}

static int report(lua_State *L, const char *filename, int status)
{
	if (status != LUA_OK && !lua_isnil(L, -1)) {
		const char *msg = lua_tostring(L, -1);
		if (msg == NULL)
			msg = "(error object is not a string)";
		fprintf(stderr, "fileName: %s, error: %s\n", filename, msg);

		lua_pop(L, 1);
		/* force a complete garbage collection in case of errors */
		lua_gc(L, LUA_GCCOLLECT, 0);
	}
	return status;
}

string LuaScript::lua_runscript(lua_State* L, const char *filename,
				const char *fn, const char *func, vector<string> &args)
{
	int i, status;
	int argc = (int)args.size();

	string ret;

	if (luaL_dostring(L, fn) != LUA_OK) {
		printf("%s\n%s.\n", fn, lua_tostring(L, -1));
		return ret;
	}

	lua_getglobal(L, func);

	for (i=0; i < argc; i++) {
		lua_pushstring(L, args[i].c_str());
	}

	// 下面的第二个参数表示带调用的lua函数存在argc个参数。
	// 第三个参数表示即使带调用的函数存在多个返回值，那么也只有一个在执行后会被压入栈中。
	// lua_pcall调用后，虚拟栈中的函数参数和函数名均被弹出。
	status = docall(L, argc, 1);
	report(L, filename, status);
	if (status != LUA_OK) {
#if TEST
		printf("%s(", func);
		for (i = 0; i < argc - 1; i++)
			printf("\"%s\", ", args[i].c_str());

		if (argc > 0)
			printf("\"%s\")\n", args[argc - 1].c_str());
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

	if (r) {
		if (strcmp(r, "null") == 0)
			r = "";
		ret.assign(r);
	}

	lua_pop(L, -1);

	return ret;
}

static const luaL_Reg lualibs[] = {
	{"_G"           , luaopen_base      },
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
		lua_pop(L, 1);
	}
}

LuaScript::LuaScript()
{
}

LuaScript::~LuaScript()
{
}

LuaScript& LuaScript::Instance()
{
	static LuaScript _lua;

	return _lua;
}

string LuaScript::RunScript(vector<string> &args, const char *name, const char *fname)
{
	string code, ret;

	if ( GetScript(name, code)) {
		lua_State *L = luaL_newstate();
		if (L) {
			luaL_openmini(L);
			ret = lua_runscript(L, name, code.c_str(), fname, args);
			lua_close(L);
		}
	}

	return ret;
}

bool script_decrypt(string& text)
{
	for (int i=0; i < text.length(); i++) {
		text[i] = text[i] ^ 0x4A;
	}

	return true;
}

bool LuaScript::GetScript(const char *name, string &text)
{
	map<string ,Script>::iterator it = scripts.find(name);
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

	if (kola.UrlGet(url + name, text) == true) {
		script_decrypt(text);
		scripts.insert(pair<string, Script>(name, Script(text)));
		return true;
	}

	printf("Not found script %s\n", name);
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

	directText = false;

	if (js)
		LoadFromJson(js);
}

ScriptCommand::~ScriptCommand()
{
}

void ScriptCommand::DelParams(int count)
{
	for (int i=0; i < count; i++)
		args.pop_back();
}

void ScriptCommand::AddParams(int arg)
{
	char buffer[64];

	sprintf(buffer, "%d", arg);

	AddParams(buffer);
}

void ScriptCommand::AddParams(const char *arg)
{
	args.push_back(arg);
}

bool ScriptCommand::LoadFromJson(json_t *js)
{
	bool ret;

	// 直接值
	json_t *tx = json_geto(js ,"text");
	if (tx != NULL) {
		if (json_is_string(tx))
			text = json_string_value(tx);
		else
			json_dump_str(tx, text);

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
		size_t count = json_array_size(params);
		for (int i = 0; i < count; i++) {
			json_t *value = json_array_get(params, i);

			if (json_is_string(value))
				AddParams(json_string_value(value));
			else if (json_is_integer(value)) {
				char buf[128];
				sprintf(buf, "%lld", json_integer_value(value));

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
		ret = lua.RunScript(args, script_name.c_str(), func_name.c_str());
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
