#!/bin/bash

# Script to download pre-built libcurl, zlib, and minizip into history_stealer/deps
# Run from inside history_stealer folder

set -e  # Exit on error

# Current directory (history_stealer)
BASE_DIR="$(pwd)"
DEST_DIR="$BASE_DIR/deps"
echo "Destination directory: $DEST_DIR"

# Create deps folder
mkdir -p "$DEST_DIR"

# Temporary download directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download pre-built zlib
echo "Downloading zlib..."
curl -L -o mingw-w64-x86_64-zlib-1.3.1-1-any.pkg.tar.zst https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-zlib-1.3.1-1-any.pkg.tar.zst
tar --zstd -xf mingw-w64-x86_64-zlib-1.3.1-1-any.pkg.tar.zst
cp mingw64/lib/libz.a "$DEST_DIR/"
cp mingw64/include/zlib.h "$DEST_DIR/"
cp mingw64/include/zconf.h "$DEST_DIR/"

# Download zlib source for minizip headers and build libminizip
echo "Downloading and building minizip..."
curl -L -o zlib-1.3.1.tar.gz https://zlib.net/zlib-1.3.1.tar.gz
tar -xzf zlib-1.3.1.tar.gz
cd zlib-1.3.1/contrib/minizip
x86_64-w64-mingw32-gcc -c *.c -I../../ -O2 -DWIN32
x86_64-w64-mingw32-ar rcs libminizip.a *.o
cp libminizip.a "$DEST_DIR/"
cp zip.h "$DEST_DIR/"
cd ../../..

# Download pre-built libcurl
echo "Downloading libcurl..."
curl -L -o mingw-w64-x86_64-curl-8.10.1-1-any.pkg.tar.zst https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-curl-8.10.1-1-any.pkg.tar.zst
tar --zstd -xf mingw-w64-x86_64-curl-8.10.1-1-any.pkg.tar.zst
cp mingw64/lib/libcurl.a "$DEST_DIR/"
mkdir -p "$DEST_DIR/curl"
cp -r mingw64/include/curl/* "$DEST_DIR/curl/"

# Cleanup
echo "Cleaning up..."
cd ..
rm -rf "$TEMP_DIR"

echo "Dependencies placed in $DEST_DIR:"
ls -l "$DEST_DIR"
echo "Done! Ready to compile main.c."