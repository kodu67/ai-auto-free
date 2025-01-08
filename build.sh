#!/bin/bash

set -e

echo "==> Gerekli paketler yükleniyor..."
pip install -r requirements.txt
pip install pyinstaller

echo "==> Temizlik yapılıyor..."
rm -rf build dist

echo "==> PyInstaller ile derleniyor..."
pyinstaller --clean --noconfirm build.spec

echo "==> Çıktı dizini kontrol ediliyor..."
if [ -f "dist/AI Auto Free" ]; then
    echo "==> Build başarılı: dist/AI Auto Free"
else
    echo "==> Build başarısız!"
    exit 1
fi
