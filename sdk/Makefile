all:
	g++ -O0 -g -o a \
		httplib.c base64.cpp \
		pcre.cpp kola.cpp album.cpp filter.cpp main.cpp \
		-ljansson -D_DEBUG -lpcre -lssl -lcrypto -pthread -lz
