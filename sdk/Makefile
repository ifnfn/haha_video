LUA=export_kola.cpp script.cpp -Ilua/src -Llua -llua

all:
	g++ -O0 -g -o a -Wno-deprecated-declarations -DTEST=0 \
		$(LUA) weather.cpp player.cpp resolution.cpp json.cpp http.cpp \
		base64.cpp threadpool.cpp resource.cpp menu.cpp stringlist.cpp \
		video.cpp task.cpp pcre.cpp kola.cpp album.cpp filter.cpp \
		update.cpp common.cpp epg.cpp main.cpp \
		-ljansson -D_DEBUG -lpcre -lcrypto -pthread -lz -lcurl -lresolv
