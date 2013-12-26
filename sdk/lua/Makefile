SRC += src/lapi.c
SRC += src/lcode.c
SRC += src/ldo.c
SRC += src/lgc.c
SRC += src/llex.c
SRC += src/loadlib.c
SRC += src/loslib.c
SRC += src/lstring.c
SRC += src/ltablib.c
SRC += src/lzio.c
SRC += src/lauxlib.c
SRC += src/ldblib.c
SRC += src/ldump.c
SRC += src/linit.c
SRC += src/lmathlib.c
SRC += src/lobject.c
SRC += src/lparser.c
SRC += src/lstrlib.c
SRC += src/ltm.c
SRC += src/lundump.c
#SRC += src/print.c
SRC += src/lbaselib.c
SRC += src/ldebug.c
SRC += src/lfunc.c
SRC += src/liolib.c
SRC += src/lmem.c
SRC += src/lopcodes.c
SRC += src/lstate.c
SRC += src/ltable.c
SRC += src/lvm.c
SRC += src/lbitlib.c
SRC += src/lcorolib.c
SRC += src/lctype.c

SRC += lua-cjson-xml/lua_cjson.c lua-cjson-xml/strbuf.c lua-cjson-xml/fpconv.c lua-cjson-xml/lua_xml.c
SRC += lua-curl/src/Lua-cURL-callback.c  lua-curl/src/Lua-cURL-multi.c  lua-curl/src/Lua-cURL-setopt.c  lua-curl/src/Lua-cURL.c \
	   lua-curl/src/Lua-cURL-getinfo.c   lua-curl/src/Lua-cURL-post.c   lua-curl/src/Lua-cURL-share.c   lua-curl/src/Lua-utility.c

LIB=liblua.a


CFLAGS +=-Isrc

default: all


include $(GXSRC_PATH)/scripts/inc.Makefile

WARNING = -Wundef -Wall

install:
	install -d  $(GXLIB_PATH)/lib
	install -d "$(GXLIB_PATH)/include"
	install -d "$(GXLIB_PATH)/include/libtu"
	install -m 644 $(LIB) $(GXLIB_PATH)/lib/
	install -m 644 *.h $(GXLIB_PATH)/include/libtu/

ckgdb:
	@rm .gdbinit
	@cp $(GXSRC_PATH)/cmock_based/ckgdb/.gdbinit .
	@cp $(GXSRC_PATH)/cmock_based/ckgdb/gdbconfig .
armgdb:
	@rm .gdbinit
	@cp $(GXSRC_PATH)/cmock_based/armgdb/.gdbinit .

arch:
	make ARCH=ckcore OS=ecos
	make ARCH=arm OS=ecos
	make ARCH=arm OS=linux
	make ARCH=i386 OS=linux
