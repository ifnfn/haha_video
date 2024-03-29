#!/bin/bash

if [ -z "$GX_PREFIX" ]; then
    GX_PREFIX="/opt/goxceed"
fi
export GX_PREFIX

CURRENT_PATH=$(cd `dirname $0`; pwd)
J="-j4"

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
                $GX_PREFIX/$ARCH-linux/include/http.hpp \
                sdk/lib/* libs/
        cp sdk/main.cpp libs/demo.cpp
    else
        _build_busbase
    fi

}

build_py() {
    python3 -b -m compileall .          -lfb -d .
    python3 -b -m compileall kola       -lfb -d .
    python3 -b -m compileall barcode    -lfb -d .
    python3 -b -m compileall engine     -lfb -d .
    python3 -b -m compileall bmemcached -lfb -d .
    python3 -b -m compileall engine/tv  -lfb -d .
    mkdir -p pyclib/kola pyclib/barcode pyclib/engine/tv pyclib/bmemcached
    mv *.pyc            pyclib/
    mv kola/*.pyc       pyclib/kola/
    mv barcode/*.pyc    pyclib/barcode/
    mv bmemcached/*.pyc pyclib/bmemcached/
    mv engine/*.pyc     pyclib/engine/
    mv engine/tv/*.pyc  pyclib/engine/tv/

    cp -af scripts templates static pyclib/
    scp -r pyclib/* root@114.215.174.227:~/kolatv/
    scp *.json all.sh super_client.py root@114.215.174.227:~/kolatv/
}

if [ $# -le 1 ]; then
    if [ "$1" = "all" ]; then
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
