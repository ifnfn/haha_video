#include <stdio.h>
#include <string.h>
#include <map>
#include <string>

extern "C" {
#include "lua.h"
}

class script {
	public:
		script() {
			time(&dtime);
		}
		script(std::string t) {
			text = t;
			time(&dtime);
		}
		std::string text;
		time_t dtime;
};

class LuaScript {
	public:
		LuaScript();
		static LuaScript& Instance();
		~LuaScript();
		std::string RunScript(int argc, const char **argv, const char *name, const char *fname="kola_main");
	private:
		lua_State *L;
		std::map<std::string, script> scripts;
		bool GetScript(const char *name, std::string &text);
};
