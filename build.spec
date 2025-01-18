# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Icon paths
WINDOWS_ICON = os.path.join('assets', 'icons', 'icon.ico')
MACOS_ICON = os.path.join('assets', 'icons', 'icon.icns')

# Base imports for all platforms
base_hiddenimports = [
    'core.app',
    'core.auth_manager',
    'core.usage',
    'utils.browser',
    'utils.email',
    'utils.machine',
    'services.cursor',
    'services.windsurf'
]

# Platform specific configurations
if sys.platform == "linux" or sys.platform == "linux2":
    datas = [
        ('src/locales/*.json', 'locales'),
        ('src/scripts/*.js', 'scripts'),
        ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
        ('src/config/settings.json', 'config'),
        (WINDOWS_ICON, 'assets/icons'),
        ('ai-auto-free-accounts.txt', '.'),
    ]
    hiddenimports = base_hiddenimports
    icon = WINDOWS_ICON

elif sys.platform == "darwin":
    datas = [
        ('src/locales/*.json', 'locales'),
        ('src/scripts/*.js', 'scripts'),
        ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
        ('src/config/settings.json', 'config'),
        (MACOS_ICON, 'assets/icons'),
        ('ai-auto-free-accounts.txt', '.'),
    ]
    hiddenimports = base_hiddenimports
    icon = MACOS_ICON

elif sys.platform == "win32":
    datas = [
        ('src/locales/*.json', 'locales'),
        ('src/scripts/*.js', 'scripts'),
        ('src/scripts/turnstilePatch', 'scripts/turnstilePatch'),
        ('src/config/settings.json', 'config'),
        (WINDOWS_ICON, 'assets/icons'),
        ('ai-auto-free-accounts.txt', '.'),
    ]
    hiddenimports = base_hiddenimports
    icon = WINDOWS_ICON

else:
    raise Exception(f"Unsupported platform: {sys.platform}")

a = Analysis(
    ['main.py'],
    pathex=['src', os.path.abspath('.')],
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
