#!/bin/bash

# Script to generate ssh key pair and setup authorization with box

if test -z "$1"
then
    echo "usage: $0 box-ip"
    exit 1
fi
host="$1"

set -xe

key="$HOME/.ssh/id_rsa"
if test ! -f "$key"; then
    ssh-keygen -N "" -f "$key"
fi
ssh-copy-id "root@${host}"
