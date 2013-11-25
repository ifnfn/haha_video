LUA=export_kola.cpp script.cpp -Ilua/src -Llua -llua

all:
	g++ -O0 -g -o a -Wno-deprecated-declarations \
		$(LUA) httplib.cpp base64.cpp threadpool.cpp \
		menu.cpp stringlist.cpp video.cpp task.cpp pcre.cpp kola.cpp album.cpp filter.cpp main.cpp \
		-ljansson -D_DEBUG -lpcre -lcrypto -pthread -lz
