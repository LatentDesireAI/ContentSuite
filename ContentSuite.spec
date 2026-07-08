# PyInstaller spec — Windows one-folder build (PySide6 + Qt Multimedia).
# Run: build_release.bat

import os

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None

hiddenimports = (
    collect_submodules("core")
    + collect_submodules("tabs")
    + collect_submodules("ui")
    + [
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
    ]
)

# Qt plugins we actually need (skip QML / SQL drivers — saves ~400 MB).
_plugin_dirs = (
    "platforms",
    "styles",
    "multimedia",
    "imageformats",
    "iconengines",
)
datas: list = []
for subdir in _plugin_dirs:
    datas += collect_data_files("PySide6", subdir=os.path.join("plugins", subdir))
datas += collect_data_files("PIL")

binaries = collect_dynamic_libs("PySide6")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6.scripts"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ContentSuite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ContentSuite",
)