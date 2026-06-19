# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys


project_root = Path(SPECPATH).parent
python_root = Path(sys.base_prefix)

datas = [(str(project_root / "templates"), "templates")]
if (python_root / "Lib" / "tkinter").exists():
    datas.append((str(python_root / "Lib" / "tkinter"), "tkinter"))
if (python_root / "tcl").exists():
    datas.append((str(python_root / "tcl"), "tcl"))

binaries = []
for name in ("_tkinter.pyd", "tcl86t.dll", "tk86t.dll"):
    path = python_root / "DLLs" / name
    if path.exists():
        binaries.append((str(path), "."))


a = Analysis(
    [str(project_root / "fh6_sniper" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "_tkinter",
        "tkinter",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "win32timezone",
        "windows_capture",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyinstaller_tk_runtime.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FH6-Sniper",
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FH6-Sniper",
)
