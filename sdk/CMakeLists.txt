INCLUDE(cmake/toolchain.cmake)

PROJECT(kolatv CXX C)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

INCLUDE_DIRECTORIES(.)
INCLUDE_DIRECTORIES(lua/src)

AUX_SOURCE_DIRECTORY(./lua/src/           SRCS)
AUX_SOURCE_DIRECTORY(./lua/lua-cjson-xml/ SRCS)
#AUX_SOURCE_DIRECTORY(./lua/lua-curl/src/  SRCS)

ADD_GX_LIBRARY(kolatv
	${SRCS}
	album.cpp
	export_kola.cpp
	http.cpp
	pcre.cpp
	stringlist.cpp
	threadpool.cpp
	base64.cpp
	filter.cpp
	kola.cpp
	menu.cpp
	script.cpp
	task.cpp
	video.cpp
	json.cpp
)

SET(CMAKE_BUILD_TYPE "Debug")
# SET(CMAKE_BUILD_TYPE "Release")

ADD_DEFINITIONS(-DTEST=0 -D_FILE_OFFSET_BITS=64 -D_LARGEFILE64_SOURCE -Wno-deprecated-declarations)

###############################################################################
# 编译可执行程序
###############################################################################
# test
SET(CMAKE_EXE_LINKER_FLAGS "--static")
ADD_EXECUTABLE(kola main.cpp)
TARGET_LINK_LIBRARIES(kola kolatv jansson pcre crypto z ${GXCORE_LIB} dl pthread curl z)

INSTALL(FILES kola.hpp DESTINATION ${GOXCEED_PATH}/include)
