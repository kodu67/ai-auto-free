# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Icon yollarını belirle
WINDOWS_ICON = os.path.join('assets', 'icons', 'icon.ico')
MACOS_ICON = os.path.join('assets', 'icons', 'icon.icns')

# Ortak veri dosyaları
common_datas = [
    ('src/locales', 'locales'),
    ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
    ('src/config/settings.json', 'src/config'),
    ('ai-auto-free-accounts.txt', '.'),
    ('src', 'src')  # Tüm src klasörünü kopyala
]

# Ortak gizli importlar
common_imports = [
    'src',  # src paketinin kendisi
    'src.auth',
    'src.config',
    'src.core',
    'src.services',
    'src.utils',
    'src.auth.cursor_auth',
    'src.auth.windsurf_auth',
    'src.auth.machine_id',
    'src.core.app',
    'src.services.browser_service',
    'src.services.email_service',
    'src.utils.helper',
    'src.utils.locale',
    'src.utils.logger',
    'src.utils.storage',
    'src.utils.usage',
    'src.config.user_settings',
    'src.config.constants',
    'src.config.settings'
]

# İşletim sistemine göre özelleştirmeler
if sys.platform == "win32":
    datas = common_datas + [(WINDOWS_ICON, 'assets/icons')]
    icon = WINDOWS_ICON
    console = True
elif sys.platform == "darwin":
    datas = common_datas + [(MACOS_ICON, 'assets/icons')]
    icon = MACOS_ICON
    console = True
elif sys.platform.startswith("linux"):
    datas = common_datas + [(WINDOWS_ICON, 'assets/icons')]
    icon = WINDOWS_ICON
    console = True
else:
    raise Exception(f"Desteklenmeyen işletim sistemi: {sys.platform}")

a = Analysis(
    ['main.py'],
    pathex=['src', os.path.abspath('src')],  # Mutlak yol ekle
    binaries=[],
    datas=datas,
    hiddenimports=common_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect all files
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
    console=console,
    icon=icon,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)

# macOS için ek yapılandırma
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name='AI Auto Free.app',
        icon=MACOS_ICON,
        bundle_identifier='com.aifree.app',
        info_plist={
            'CFBundleShortVersionString': '1.1.1',
            'CFBundleVersion': '1.1.1',
            'NSHighResolutionCapable': 'True'
        }
    )
