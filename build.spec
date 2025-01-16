# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Icon yollarını belirle
WINDOWS_ICON = os.path.join('assets', 'icons', 'icon.ico')
MACOS_ICON = os.path.join('assets', 'icons', 'icon.icns')

# İşletim sistemine göre özelleştirmeler
if sys.platform == "linux" or sys.platform == "linux2":
    # Linux için özel ayarlar
    datas = [
        ('src/locales/*.json', 'locales'),
        ('src/scripts/*.js', 'scripts'),
        ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
        ('src/config/settings.json', 'config'),
        (WINDOWS_ICON, 'assets/icons'),  # Icon'u assets klasörüne kopyala
        ('ai-auto-free-accounts.txt', '.'),  # Log dosyası ana dizine kopyalanacak
    ]
    hiddenimports = [
        'src.utils.browser_utils',
        'src.auth.cursor_auth',
        'src.services.cursor_pro_keep_alive',
        'src.utils.get_email_code',
        'src.utils.locale_manager',
        'src.core.logo',
        'src.utils.machine_id_reset',
        'src.auth.windsurf_auth',
        'src.core.app'
    ]
    icon = WINDOWS_ICON

elif sys.platform == "darwin":
    # macOS için özel ayarlar
    datas = [
        ('src/locales/*.json', 'locales'),
        ('src/scripts/*.js', 'scripts'),
        ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
        ('src/config/settings.json', 'config'),
        (MACOS_ICON, 'assets/icons'),  # Icon'u assets klasörüne kopyala
        ('ai-auto-free-accounts.txt', '.'),  # Log dosyası ana dizine kopyalanacak
    ]
    hiddenimports = [
        'src.utils.browser_utils',
        'src.auth.cursor_auth',
        'src.services.cursor_pro_keep_alive',
        'src.utils.get_email_code',
        'src.utils.locale_manager',
        'src.utils.machine_id_reset',
        'src.auth.windsurf_auth',
        'src.core.app'
    ]
    icon = MACOS_ICON

elif sys.platform == "win32":
    # Windows için özel ayarlar
    datas = [
        ('src/locales/*.json', 'locales'),
        ('src/scripts/*.js', 'scripts'),
        ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
        ('src/config/settings.json', 'config'),
        (WINDOWS_ICON, 'assets/icons'),  # Icon'u assets klasörüne kopyala
        ('ai-auto-free-accounts.txt', '.'),  # Log dosyası ana dizine kopyalanacak
    ]
    hiddenimports = [
        'src.utils.browser_utils',
        'src.auth.cursor_auth',
        'src.services.cursor_pro_keep_alive',
        'src.utils.get_email_code',
        'src.utils.locale_manager',
        'src.utils.machine_id_reset',
        'src.auth.windsurf_auth',
        'src.core.app'
    ]
    icon = WINDOWS_ICON

else:
    raise Exception(f"Desteklenmeyen işletim sistemi: {sys.platform}")

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI Auto Free',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=icon,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
