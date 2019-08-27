#!/bin/sh

PYTHON=python3

PREFIX=/usr/local
#PREFIX=/usr
FILES=files.txt

if ! $PYTHON -c 'import daemon' 2>/dev/null; then
    echo "Installing ${PYTHON}-daemon"
    sudo apt-get install ${PYTHON}-daemon
fi

echo "Installing to $PREFIX, keeping list of files in $FILES"
echo

sudo $PYTHON setup.py install --prefix "$PREFIX" --record "$FILES"

echo
echo "Uninstall with 'cat $FILES | sudo xargs rm -rf'"
