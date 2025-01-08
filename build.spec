# -*- mode: python ; coding: utf-8 -*-

import sys

block_cipher = None

# İşletim sistemine göre özelleştirmeler
if sys.platform == "linux" or sys.platform == "linux2":
    # Linux için özel ayarlar
    datas = [
        ('locales/*.json', 'locales'),
        ('logo.py', '.'),
        ('turnstilePatch', 'turnstilePatch'),
    ]
    hiddenimports = [
        'browser_utils',
        'cursor_auth_manager',
        'cursor_pro_keep_alive',
        'get_email_code',
        'locale_manager',
        'logo',
        'machine_id_reset',
        'windsurf_account_creator',
    ]
elif sys.platform == "darwin":
    # macOS için özel ayarlar
    datas = [
        ('locales/*.json', 'locales'),
        ('logo.py', '.'),
        ('turnstilePatch', 'turnstilePatch'),
    ]
    hiddenimports = [
        'browser_utils',
        'cursor_auth_manager',
        'cursor_pro_keep_alive',
        'get_email_code',
        'locale_manager',
        'logo',
        'machine_id_reset',
        'windsurf_account_creator',
    ]
elif sys.platform == "win32":
    # Windows için özel ayarlar
    datas = [
        ('locales/*.json', 'locales'),
        ('logo.py', '.'),
        ('turnstilePatch', 'turnstilePatch'),
    ]
    hiddenimports = [
        'browser_utils',
        'cursor_auth_manager',
        'cursor_pro_keep_alive',
        'get_email_code',
        'locale_manager',
        'logo',
        'machine_id_reset',
        'windsurf_account_creator',
    ]
else:
    raise Exception(f"Desteklenmeyen işletim sistemi: {sys.platform}")

a = Analysis(
    ['main.py'],
    pathex=[],
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
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
