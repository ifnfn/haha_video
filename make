#!/bin/bash

if [ -z "$GX_PREFIX" ]; then
    GX_PREFIX="/opt/goxceed"
fi
export GX_PREFIX

CURRENT_PATH=$(cd `dirname $0`; pwd)

function _build_busbase() {
    BUILD_PATH=build_x
    rm -rf $BUILD_PATH
    mkdir -p $BUILD_PATH
    cd     $BUILD_PATH
    pwd

    if [ $# -ge 1 ]; then
        export CROSS_TOOLCHAIN=$1
    fi
    cmake $CURRENT_PATH/sdk || exit 1
    make $J || exit 1
    make install || exit 1
    cd $CURRENT_PATH
}

# build [csky|arm]
build() {
    ARCH=$1

    if [ "$ARCH" = "csky" ] || [ "$ARCH" = "arm" ]; then
        CROSS_TOOLCHAIN=$ARCH-linux-
        _build_busbase $CROSS_TOOLCHAIN $ARCH-$OS

        mkdir -p libs
        cp $GX_PREFIX/$ARCH-linux/lib/libkolatv.a \
                $GX_PREFIX/$ARCH-linux/include/kola.hpp \
                sdk/lib/* libs/
        cp sdk/main.cpp libs/demo.cpp
    else
        _build_busbase
    fi

}

build_py() {
    python3 -b -m compileall . -lfb -d .
    mkdir -p pyclib
    mv *.pyc pyclib/
}

if [ $# -le 1 ]; then
    if [ "$1" = "all" ]; then
#        build csky
        build_py
    elif [ "$1" = "clean" ]; then
        rm -rf build
    else
        build $1
    fi
    exit 1
else
    echo "./build [debug|release] [clean] [all] [csky|arm]"
    echo "    eg: ./build csky"
    echo "        ./build arm"
    echo "./build all"
    echo "./build clean"
fi

build $@
