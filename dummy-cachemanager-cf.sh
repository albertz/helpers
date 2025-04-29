#!/bin/bash

DEST=/var/tmp/$(whoami)/cm/
SRC=$(realpath $1)

if [[ $SRC == $DEST* ]]; then
	echo $SRC
	exit
fi

mkdir -p $DEST 1>&2

rsync -avR $SRC $DEST 1>&2

echo $DEST/$SRC
