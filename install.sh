#!/bin/sh

PREFIX=/usr/local
#PREFIX=/usr
FILES=files.txt

echo "Installing to $PREFIX, keeping list of files in $FILES"
echo

sudo python setup.py install --prefix "$PREFIX" --record "$FILES"

echo
echo "Uninstall with 'cat $FILES | sudo xargs rm -rf'"