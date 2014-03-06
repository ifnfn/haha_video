#ifndef SCRIPT_HPP
#define SCRIPT_HPP

#include <stdio.h>
#include <string.h>
#include <map>
#include <string>

#include "lua.hpp"
#include "jansson.h"

using namespace std;

class Script {
public:
	Script() {
		time(&dtime);
	}
	Script(string t) {
		text = t;
		time(&dtime);
	}

	string text;
	time_t dtime;
};

class LuaScript {
public:
	static LuaScript& Instance();
	string RunScript(vector<string> &args, const char *name, const char *fname="kola_main");
private:
	map<string, Script> scripts;
	bool GetScript(const char *name, string &text);
	string lua_runscript(lua_State* L, const char *filename,
			     const char *fn, const char *func, vector<string> &args);
};

#endif
