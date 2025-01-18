#!/bin/bash

set -e

echo "==> Installing required packages..."
pip install -r requirements.txt
pip install pyinstaller

echo "==> Cleaning up..."
rm -rf build dist

echo "==> Building with PyInstaller..."
pyinstaller --clean --noconfirm build.spec

echo "==> Checking output directory..."
if [ "$(uname)" == "Darwin" ]; then
    # macOS için kontrol
    if [ -d "dist/AI Auto Free.app" ]; then
        echo "==> Build successful: dist/AI Auto Free.app"
    else
        echo "==> Build failed!"
        exit 1
    fi
else
    # Linux için kontrol
    if [ -f "dist/AI Auto Free" ]; then
        echo "==> Build successful: dist/AI Auto Free"
    else
        echo "==> Build failed!"
        exit 1
    fi
fi
