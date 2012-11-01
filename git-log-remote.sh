#!/bin/bash

[ "$1" = "" ] && echo "usage: $0 <gitrepo-url>" && exit 1

tmpdir=`mktemp -d /tmp/git-tmp.XXXXXX` || exit 1
echo "temp dir: $tmpdir"

pushd "$tmpdir"
git clone --depth=1 -n "$1" .
git log
popd

rm -rf "$tmpdir"
