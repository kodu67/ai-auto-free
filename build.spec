# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import site
from pathlib import Path

block_cipher = None

# Icon yollarını belirle
WINDOWS_ICON = os.path.join("assets", "icons", "icon.ico")
MACOS_ICON = os.path.join("assets", "icons", "icon.icns")

# mitmdump'ı bul
def find_mitmdump():
    # Site packages'ları kontrol et
    site_packages = site.getsitepackages()
    for site_package in site_packages:
        if sys.platform == "win32":
            mitmdump_path = os.path.join(site_package, "mitmproxy", "tools", "mitmdump.exe")
        else:
            mitmdump_path = os.path.join(site_package, "mitmproxy", "tools", "mitmdump")

        if os.path.exists(mitmdump_path):
            return [(mitmdump_path, ".")]

    return []

# Ortak veri dosyaları
common_datas = [
    ("src/locales", "locales"),
    ("src/scripts/turnstilePatch", "scripts/turnstilePatch"),
    ("src/config/settings.json", "src/config"),
    ("src", "src"),  # Tüm src klasörünü kopyala
] + find_mitmdump()  # mitmdump'ı ekle

# Ortak gizli importlar
common_imports = [
    "src",  # src paketinin kendisi
    "src.auth",
    "src.config",
    "src.core",
    "src.services",
    "src.utils",
    "src.auth.cursor_auth",
    "src.auth.windsurf_auth",
    "src.auth.machine_id",
    "src.core.app",
    "src.core.ui",
    "src.services.browser_service",
    "src.services.email_service",
    "src.services.proxy",
    "src.services.proxy.cursor_interceptor",
    "src.services.proxy.proxy_manager",
    "src.services.proxy.install_cert",
    "src.services.proxy.proxy_service",
    "src.utils.helper",
    "src.utils.locale",
    "src.utils.logger",
    "src.utils.storage",
    "src.utils.usage",
    "src.config.user_settings",
    "src.config.constants",
    "src.config.settings",
    "elevate",
    "customtkinter",
    "mitmproxy",
    "pyperclip",
]

# İşletim sistemine göre özelleştirmeler
if sys.platform == "win32":
    datas = common_datas + [(WINDOWS_ICON, "assets/icons")]
    icon = WINDOWS_ICON
    console = False
elif sys.platform == "darwin":
    datas = common_datas + [(MACOS_ICON, "assets/icons")]
    icon = MACOS_ICON
    console = False
elif sys.platform.startswith("linux"):
    datas = common_datas + [(WINDOWS_ICON, "assets/icons")]
    icon = WINDOWS_ICON
    console = False
else:
    raise Exception(f"Desteklenmeyen işletim sistemi: {sys.platform}")

a = Analysis(
    ["main.py"],
    pathex=["src", os.path.abspath("src")],  # Mutlak yol ekle
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
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AI Auto Free",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

# macOS için ek yapılandırma
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="AI Auto Free.app",
        icon=MACOS_ICON,
        bundle_identifier="com.aifree.app",
        info_plist={
            "CFBundleShortVersionString": "1.1.3",
            "CFBundleVersion": "1.1.3",
            "NSHighResolutionCapable": "True",
        },
    )
