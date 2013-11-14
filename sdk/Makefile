LUA=export_kola.c lua_test.c -Ilua/src -Llua -llua

all:
	g++ -O0 -g -o a \
		$(LUA) httplib.cpp base64.cpp threadpool.cpp \
		menu.cpp stringlist.cpp video.cpp task.cpp pcre.cpp kola.cpp album.cpp filter.cpp main.cpp \
		-ljansson -D_DEBUG -lpcre -lcrypto -pthread -lz
