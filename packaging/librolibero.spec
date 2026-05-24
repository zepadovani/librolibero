# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec do librolibero GUI.

Uso:
    macOS / Linux:  pyinstaller packaging/librolibero.spec
    Windows:        pyinstaller packaging\\librolibero.spec

O artefato gerado fica em dist/:
    macOS   → dist/librolibero.app
    Windows → dist/librolibero/librolibero.exe
    Linux   → dist/librolibero/librolibero
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Raiz do projeto (um nível acima de packaging/)
ROOT = Path(SPECPATH).parent  # noqa: F821 — SPECPATH injetado pelo PyInstaller

# ── PySide6 (plugins Qt, translations, binários nativos) ──────────────────
pyside6_datas, pyside6_binaries, pyside6_hidden = collect_all("PySide6")

# ── Hidden imports que o PyInstaller costuma perder ────────────────────────
hidden_imports = [
    *pyside6_hidden,
    *collect_submodules("librolibero"),
    # isbnlib usa metaprogramação interna
    "isbnlib",
    "isbnlib.dev",
    "isbnlib.dev._bibformatters",
    "isbnlib.dev.api",
    # fitz = pymupdf
    "fitz",
    # ebooklib
    "ebooklib",
    "ebooklib.epub",
    # pyzotero
    "pyzotero",
    "pyzotero.zotero",
    # dotenv
    "dotenv",
    # tomli (Python < 3.11)
    "tomli",
]

# ── Ícones ─────────────────────────────────────────────────────────────────
ICON_ICNS = str(ROOT / "packaging" / "icons" / "librolibero.icns")
ICON_ICO  = str(ROOT / "packaging" / "icons" / "librolibero.ico")
icon = ICON_ICNS if sys.platform == "darwin" else ICON_ICO

# ── Analysis ───────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "packaging" / "entrypoint_gui.py")],
    pathex=[str(ROOT)],
    binaries=pyside6_binaries,
    datas=[
        *pyside6_datas,
        # Ícones SVG usados dentro da GUI (logo nas telas)
        (str(ROOT / "librolibero" / "icon"), "librolibero/icon"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Excluir módulos que não usamos para reduzir tamanho
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "IPython",
        "jupyter",
        "notebook",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)  # noqa: F821

# ── Executável ─────────────────────────────────────────────────────────────
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="librolibero",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # sem janela de terminal (windowed mode)
    icon=icon,
)

# ── Coleta de dependências ─────────────────────────────────────────────────
coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="librolibero",
)

# ── Bundle .app (apenas macOS) ────────────────────────────────────────────
if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name="librolibero.app",
        icon=ICON_ICNS,
        bundle_identifier="br.dev.padovani.librolibero",
        info_plist={
            "CFBundleName": "librolibero",
            "CFBundleDisplayName": "librolibero",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,  # suporte a Dark Mode
            "LSMinimumSystemVersion": "11.0",
        },
    )
