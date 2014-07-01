INCLUDE (CMakeForceCompiler)

SET(TOOLCHAIN_PREFIX $ENV{CROSS_TOOLCHAIN})
SET(CMAKE_C_COMPILER_WORKS TRUE)
SET(CMAKE_CXX_COMPILER_WORKS TRUE)

# specify the cross compiler
# the name of the target operating system
SET(CMAKE_SYSTEM_NAME Generic)

SET(GXCORE_LIB gxcore)
#ADD_DEFINITIONS(-D$ENV{ARCH} -D$ENV{ARCH}-$ENV{OS})
IF (TOOLCHAIN_PREFIX STREQUAL arm-eabi-)
	SET(ARCH ARM)
	SET(OS   ECOS)
	SET(GOXCEED_PATH $ENV{GX_PREFIX}/arm-ecos)
ELSEIF (TOOLCHAIN_PREFIX STREQUAL arm-linux- OR TOOLCHAIN_PREFIX STREQUAL arm-guoxin-linux-gnueabi-)
	SET(ARCH ARM)
	SET(OS   LINUX)
	SET(GOXCEED_PATH $ENV{GX_PREFIX}/arm-linux)
ELSEIF (TOOLCHAIN_PREFIX STREQUAL csky-elf- )
	SET(ARCH CSKY)
	SET(OS   ECOS)
	SET(GOXCEED_PATH $ENV{GX_PREFIX}/csky-ecos)
ELSEIF (TOOLCHAIN_PREFIX STREQUAL csky-linux- )
	SET(ARCH CSKY)
	SET(OS   LINUX)
	SET(GOXCEED_PATH $ENV{GX_PREFIX}/csky-linux)
	SET(FLOAT "-mhard-float")
ELSEIF (TOOLCHAIN_PREFIX STREQUAL ckcore-elf- )
	SET(ARCH CKCORE)
	SET(OS   ECOS)
	SET(GOXCEED_PATH $ENV{GX_PREFIX}/ckcore-ecos)
ELSE()
	SET(ARCH I386)
	SET(OS   LINUX)
	SET(GOXCEED_PATH /usr/local/)
	SET(GXCORE_LIB "")
ENDIF()

SET(CMAKE_C_COMPILER   ${TOOLCHAIN_PREFIX}gcc)
SET(CMAKE_CXX_COMPILER ${TOOLCHAIN_PREFIX}g++)

ADD_DEFINITIONS(-D${ARCH} -D${OS}_OS)
ADD_DEFINITIONS(-D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64)

# adjust the default behaviour of hte FIND_XXX() NEVER)
SET(CMAKE_FIND_ROOT_PATH_MODULE_PROGRAM NEVER)
SET(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
SET(CMAKE_FIND_ROOT_PATH_INCLUDE ONLY)

SET(GXSRC_PATH ${CMAKE_CURRENT_SOURCE_DIR})
SET(CMAKE_INSTALL_PREFIX ${GOXCEED_PATH} )

SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Werror -Wall -funsigned-char")
SET(CMAKE_CXX_FLAGS_DEBUG   "$ENV{CXXFLAGS} -O0 -Wall -g -ggdb -DGXDBG -DMEMORY_DEBUG ${FLOAT}")
SET(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O2 -Wall"                                         )

SET(CMAKE_C_FLAGS_DEBUG     "$ENV{CFLAGS} -O0 -Wall -g -ggdb -DGXDBG -DMEMORY_DEBUG ${FLOAT}"  )
SET(CMAKE_C_FLAGS_RELEASE   "$ENV{CFLAGS} -O2 -Wall"                                           )

INCLUDE_DIRECTORIES( ${GOXCEED_PATH}/include/    )
INCLUDE_DIRECTORIES( ${GOXCEED_PATH}/include/bus )
INCLUDE_DIRECTORIES( ${GOXCEED_PATH}/include/av  )
INCLUDE_DIRECTORIES( ${CMAKE_BINARY_DIR}         )
LINK_DIRECTORIES   ( ${GOXCEED_PATH}/lib         )

FUNCTION(ADD_GX_LIBRARY name)
	ADD_LIBRARY( ${name} ${ARGN} )
	INSTALL(TARGETS ${name}
		ARCHIVE DESTINATION ${GOXCEED_PATH}/lib)
ENDFUNCTION(ADD_GX_LIBRARY name)
