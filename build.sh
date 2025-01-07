#!/bin/bash

# Gerekli paketleri yükle
pip install -r requirements.txt
pip install pyinstaller

# Temizlik
rm -rf build dist

# PyInstaller ile build al
pyinstaller build.spec

# Çıktı dizinini kontrol et
if [ -d "dist/AI Auto Free" ]; then
    echo "Build başarılı: dist/AI Auto Free"
else
    echo "Build başarısız!"
    exit 1
fi
