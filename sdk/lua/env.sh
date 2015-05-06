export ARCH=csky
export OS=linux


CROSS_PATH=$ARCH-$OS

if [ "$CROSS_PATH" = "i386-linux" ]; then
	GX_KERNEL_PATH=/lib/modules/`uname -r`/build
else
	GX_KERNEL_PATH=/opt/goxceed/kernel-2.6.28.2-build
fi

export GX_KERNEL_PATH
export CROSS_COMPILE=$ARCH-$OS-
export GXLIB_PATH=$OPT/opt/goxceed/$CROSS_PATH
export GXSRC_PATH=`pwd`
export ECOS_REPOSITORY=$GXSRC_PATH/ecos3.0/packages

