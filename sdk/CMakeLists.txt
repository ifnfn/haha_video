INCLUDE(cmake/toolchain.cmake)

PROJECT(kolatv CXX)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

INCLUDE_DIRECTORIES(.)

AUX_SOURCE_DIRECTORY( . SRCS )

SET(SRCS
	album.cpp
	base64.cpp
	filter.cpp
	httplib.cpp
	kola.cpp
	pcre.cpp
	threadpool.cpp
	task.cpp
	video.cpp
	stringlist.cpp
	menu.cpp
)

ADD_GX_LIBRARY(kolatv
	${SRCS}
)


###############################################################################
# 编译可执行程序
###############################################################################
# test
SET(CMAKE_EXE_LINKER_FLAGS "--static")
ADD_EXECUTABLE(kola main.cpp)
TARGET_LINK_LIBRARIES(kola kolatv jansson pcre crypto z dl gxcore pthread)

INSTALL(FILES kola.hpp DESTINATION ${GOXCEED_PATH}/include)
