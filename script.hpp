#ifndef SCRIPT_HPP
#define SCRIPT_HPP

#include <stdio.h>
#include <string.h>
#include <map>
#include <string>

#include "lua.hpp"
#include "jansson.h"

using namespace std;

class script {
	public:
		script() {
			time(&dtime);
		}
		script(string t) {
			text = t;
			time(&dtime);
		}
		string text;
		time_t dtime;
};

class LuaScript {
	public:
		LuaScript();
		static LuaScript& Instance();
		~LuaScript();
		string RunScript(int argc, const char **argv, const char *name, const char *fname="kola_main");
	private:
		std::map<string, script> scripts;
		bool GetScript(const char *name, string &text);
};

#endif
