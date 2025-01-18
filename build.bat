@echo off

:: Install required packages
pip install -r requirements.txt
pip install pyinstaller

:: Clean up
rmdir /s /q build dist

:: Build with PyInstaller
pyinstaller build.spec

:: Check output directory
if exist "dist\AI Auto Free.exe" (
    echo Build successful: dist\AI Auto Free.exe
) else (
    echo Build failed!
    exit /b 1
)
