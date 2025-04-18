#!/bin/bash

DEST=/var/tmp/$(whoami)/cm/
mkdir -p $DEST 1>&2

rsync -avR $1 $DEST 1>&2

echo $DEST/$1
