SRC = \
	lapi.c lcode.c ldo.c lgc.c llex.c loadlib.c loslib.c lstring.c ltablib.c  \
	luac.c lzio.c lauxlib.c ldblib.c ldump.c linit.c lmathlib.c lobject.c     \
	lparser.c lstrlib.c ltm.c lundump.c print.c lbaselib.c ldebug.c lfunc.c   \
	liolib.c lmem.c lopcodes.c lstate.c ltable.c lvm.c

ifeq ($(CROSS_PATH), arm-ecos)
	CFLAGS +=
endif

ifeq ($(CROSS_PATH), arm-linux)
	CFLAGS +=
endif

ifeq ($(CROSS_PATH), arm-linux)
	CFLAGS += 
endif

ifeq ($(CROSS_PATH), ckcore-ecos)
	CFLAGS += -mbig-endian
endif


LIB= liblua.a

include $(GXSRC_PATH)/scripts/inc.Makefile

install: $(LIB)
	install -d  $(GXLIB_PATH)/lib
	install -d "$(GXLIB_PATH)/include"
	install -d "$(GXLIB_PATH)/include/lua"
	install -m 644 $(LIB) $(GXLIB_PATH)/lib
	install -m 644 *.h $(GXLIB_PATH)/include/lua/

