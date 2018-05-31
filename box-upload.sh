#!/bin/bash

# Script to build plugin, upload it to box and install as ipk

if test -z "$1"
then
    echo "usage: $0 box-ip [provider]"
    exit 1
fi
host="$1"

if test -n "$2"
then
    provider="$2"
else
    provider="all"
fi


set -xe
cd "$(dirname $0)"

build_dir="/tmp/iptvdream-build"
rm -rf ${build_dir} && mkdir -p ${build_dir}

export DESTDIR=${build_dir}
export PROVIDER=${provider}

make version
source version && test -n "${version}"

name=`echo "enigma2-plugin-extensions-iptvdream-${provider}" |tr A-Z a-z`
package="${name}_${version}_all.ipk"
ipk="packages/${package}"

rm -f ${ipk} && make ${ipk}
wput -u -nc ${ipk} "ftp://root@${host}/tmp/test.ipk"
ssh "root@${host}" opkg install --force-reinstall "/tmp/test.ipk"
