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
)

ADD_GX_LIBRARY(kolatv
	${SRCS}
)


###############################################################################
# 编译可执行程序
###############################################################################
# test
#ADD_EXECUTABLE(test main.cpp)
#TARGET_LINK_LIBRARIES(test kolatv jansson pcre crypto z pthread dl)

INSTALL(FILES kola.hpp DESTINATION ${GOXCEED_PATH}/include)
