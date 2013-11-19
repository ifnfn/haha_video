INCLUDE(cmake/toolchain.cmake)

PROJECT(kolatv CXX C)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

INCLUDE_DIRECTORIES(.)
INCLUDE_DIRECTORIES(lua/src)

AUX_SOURCE_DIRECTORY( .                   SRCS )
AUX_SOURCE_DIRECTORY(./lua/src/           SRCS)
AUX_SOURCE_DIRECTORY(./lua/lua-cjson-xml/ SRCS)

ADD_GX_LIBRARY(kolatv
	${SRCS}
)
ADD_DEFINITIONS(-D_FILE_OFFSET_BITS=64 -D_LARGEFILE64_SOURCE)

###############################################################################
# 编译可执行程序
###############################################################################
# test
SET(CMAKE_EXE_LINKER_FLAGS "--static")
ADD_EXECUTABLE(kola main.cpp)
TARGET_LINK_LIBRARIES(kola kolatv jansson pcre crypto z ${GXCORE_LIB} dl pthread)

INSTALL(FILES kola.hpp DESTINATION ${GOXCEED_PATH}/include)
