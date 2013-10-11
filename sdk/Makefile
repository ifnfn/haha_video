all:
	g++ -O0 -g -o a \
		httplib.cpp base64.cpp threadpool.cpp \
		pcre.cpp kola.cpp album.cpp filter.cpp main.cpp \
		-ljansson -D_DEBUG -lpcre -lssl -lcrypto -pthread -lz
