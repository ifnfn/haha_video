#include <stdio.h>
#include <string.h>
#include <stdarg.h>

extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
int luaopen_kola(lua_State *L);
int luaopen_cjson(lua_State *L);
}

const char *call_function(lua_State* L, const char *fn, const char *func, ...)
{
	va_list argp;
	int argc = 0;

	//if (luaL_dostring(L,lua_function_code))
	if (luaL_dofile(L, fn)) {
		printf("Failed to run lua code.\n");
		return NULL;
	}

	lua_getglobal(L, func);

	va_start(argp, func);
	while(argp) {
		char *tmp = va_arg(argp, char *);
		if (tmp == NULL)
			break;
		lua_pushstring(L, tmp);
		argc++;
	}
	va_end(argp);

	//下面的第二个参数表示带调用的lua函数存在两个参数。
	//第三个参数表示即使带调用的函数存在多个返回值，那么也只有一个在执行后会被压入栈中。
	//lua_pcall调用后，虚拟栈中的函数参数和函数名均被弹出。
	if (lua_pcall(L, argc, 1,0)) {
		printf("error is %s.\n",lua_tostring(L,-1));
		return NULL;
	}

	//此时结果已经被压入栈中。
	if (!lua_isstring(L, -1)) {
		printf("function 'add' must return a string.\n");
		lua_pop(L,-1);
		return NULL;
	}

	const char *ret = lua_tostring(L,-1);
	if (ret)
		ret = strdup(ret);

	lua_pop(L,-1);

	return ret;
}

static const luaL_Reg lualibs[] = {
	{""             , luaopen_base}   ,
	{LUA_TABLIBNAME , luaopen_table}  ,
	{LUA_IOLIBNAME  , luaopen_io}     ,
	{LUA_OSLIBNAME  , luaopen_os}     ,
	{LUA_STRLIBNAME , luaopen_string} ,
	{"kola"         , luaopen_kola}   ,
	{"cjson"        , luaopen_cjson}  ,

	//{LUA_LOADLIBNAME, luaopen_package},
	//{LUA_MATHLIBNAME, luaopen_math},
	//{LUA_DBLIBNAME, luaopen_debug},
	{NULL, NULL}
};


static void luaL_openmini(lua_State *L) {
	const luaL_Reg *lib = lualibs;
	for (; lib->func; lib++) {
		lua_pushcfunction(L, lib->func);
		lua_pushstring(L, lib->name);
		lua_call(L, 1, 0);
	}
}

//const char* lua_function_code = "function add(x,y) a=kola.wget('http://www.china.com') return a end";

int lua_main()
{
	lua_State* L = luaL_newstate();
	luaL_openmini(L);
	const char * ret = call_function(L, "test.lua", "kola_main", "http://www.google.com", NULL);
	printf("ret= %s\n", ret);
	lua_close(L);
	return 0;
}


