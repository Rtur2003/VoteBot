# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

project_root = Path(__file__).resolve().parents[1]
app_dir = project_root / "Code_EXE" / "Votryx"

datas = [
    (str(project_root / "docs" / "screenshots"), "docs/screenshots"),
    (str(app_dir / "config.json"), "."),
]

chromedriver = project_root / "chromedriver.exe"
if chromedriver.exists():
    datas.append((str(chromedriver), "."))

hiddenimports = [
    "pystray",
    "PIL.Image",
    "PIL.ImageTk",
]

a = Analysis(
    [str(app_dir / "VotryxApp.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VOTRYX",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="VOTRYX",
)
