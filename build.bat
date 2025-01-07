@echo off

:: Gerekli paketleri yükle
pip install -r requirements.txt
pip install pyinstaller

:: Temizlik
rmdir /s /q build dist

:: PyInstaller ile build al
pyinstaller build.spec

:: Çıktı dizinini kontrol et
if exist "dist\AI Auto Free" (
    echo Build başarılı: dist\AI Auto Free
) else (
    exit /b 1
)
