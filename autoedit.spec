# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "src" / "autoedit" / "assets"), "assets"),
]
datas += collect_data_files("faster_whisper")
datas += collect_data_files("ctranslate2", include_py_files=False)

hiddenimports = collect_submodules("faster_whisper")
hiddenimports += ["av", "PIL.Image", "PIL.ImageFile", "huggingface_hub"]
hiddenimports += ["tokenizers", "onnxruntime"]

excludes = [
    "tkinter",
    "unittest",
    "pydoc",
    "doctest",
    "pytest",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtQuick",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.QtMultimedia",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtPdf",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtNetwork",
]

qt_drop = (
    "opengl32sw.dll",
    "Qt6Quick",
    "Qt6Qml",
    "Qt6QmlModels",
    "Qt6QmlWorkerScript",
    "Qt6Pdf",
    "Qt6VirtualKeyboard",
    "translations",
    "qml",
    "assetimporters",
    "canbus",
    "designer",
    "geometryloaders",
    "qmltooling",
    "sceneparsers",
    "texttospeech",
    "virtualkeyboard",
    "nfc",
    "position",
    "sensors",
)


def keep(entry) -> bool:
    name = Path(entry[0]).name
    if name.startswith(tuple(t + "." for t in qt_drop)) or name in qt_drop:
        return False
    return True


a = Analysis(
    [str(ROOT / "src" / "autoedit" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

a.binaries = [b for b in a.binaries if keep(b)]
a.datas = [d for d in a.datas if keep(d)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="autoedit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "src" / "autoedit" / "assets" / "logo.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="autoedit",
)
