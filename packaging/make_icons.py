#!/usr/bin/env python3
"""Gera librolibero.icns (macOS) e librolibero.ico (Windows)
a partir de librolibero/icon/librolibero_quad.svg (já quadrado: viewBox 60×60).

Pré-requisito:
    pip install Pillow
    brew install librsvg   # fornece rsvg-convert (macOS)
    # OU: inkscape disponível no PATH

Uso:
    python packaging/make_icons.py

Saída:
    packaging/icons/librolibero.icns
    packaging/icons/librolibero.ico
    packaging/icons/librolibero_512.png   ← prévia 512×512
"""

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("❌  Pillow não encontrado. Instale com: pip install Pillow")

ROOT      = Path(__file__).parent.parent
SVG_SRC   = ROOT / "librolibero" / "icon" / "librolibero_quad.svg"
ICONS_DIR = Path(__file__).parent / "icons"
ICONS_DIR.mkdir(exist_ok=True)

ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]
ICO_SIZES  = [16, 24, 32, 48, 64, 128, 256]


# ── Renderização SVG → PNG ─────────────────────────────────────────────────

def _render_svg(svg: Path, out: Path, size: int) -> None:
    """Renderiza o SVG quadrado em PNG size×size."""
    if shutil.which("rsvg-convert"):
        subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(out), str(svg)],
            check=True,
        )
    elif shutil.which("inkscape"):
        subprocess.run(
            ["inkscape", f"--export-filename={out}",
             f"--export-width={size}", f"--export-height={size}", str(svg)],
            check=True,
        )
    else:
        sys.exit(
            "❌  rsvg-convert ou inkscape necessário.\n"
            "    macOS: brew install librsvg"
        )


def _load(size: int, base_png: Path) -> Image.Image:
    img = Image.open(base_png).convert("RGBA")
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
    return img


# ── ICO ────────────────────────────────────────────────────────────────────

def build_ico(base_png: Path, out: Path) -> None:
    imgs = [_load(s, base_png) for s in ICO_SIZES]
    imgs[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=imgs[1:],
    )
    print(f"✓  {out}")


# ── ICNS (macOS) ───────────────────────────────────────────────────────────

def _icns_pure(base_png: Path, out: Path) -> None:
    OSTYPE = {
        16: b"ic04", 32: b"ic05", 64: b"ic12",
        128: b"ic07", 256: b"ic08", 512: b"ic09", 1024: b"ic10",
    }
    chunks = b""
    for sz in ICNS_SIZES:
        frame = _load(sz, base_png)
        with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as buf:
            frame.save(buf, format="PNG")
            buf.seek(0)
            data = buf.read()
        chunks += OSTYPE[sz] + struct.pack(">I", 8 + len(data)) + data

    out.write_bytes(b"icns" + struct.pack(">I", 8 + len(chunks)) + chunks)
    print(f"✓  {out}  (sem iconutil — compatibilidade básica)")


def build_icns(base_png: Path, out: Path) -> None:
    if sys.platform != "darwin" or not shutil.which("iconutil"):
        _icns_pure(base_png, out)
        return

    with tempfile.TemporaryDirectory(suffix=".iconset") as iconset:
        ip = Path(iconset)
        for sz in ICNS_SIZES:
            _load(sz, base_png).save(ip / f"icon_{sz}x{sz}.png")
            if sz <= 512:
                _load(sz, base_png).save(ip / f"icon_{sz // 2}x{sz // 2}@2x.png")

        subprocess.run(
            ["iconutil", "-c", "icns", str(ip), "-o", str(out)],
            check=True,
        )
    print(f"✓  {out}  (iconutil)")


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not SVG_SRC.exists():
        sys.exit(f"❌  SVG não encontrado: {SVG_SRC}")

    print(f"Fonte: {SVG_SRC}\n")

    # Renderiza o SVG em 1024×1024 uma única vez
    base_png = ICONS_DIR / "_base_1024.png"
    print("Renderizando SVG em 1024×1024…")
    _render_svg(SVG_SRC, base_png, size=1024)

    # PNG de referência
    _load(512, base_png).save(ICONS_DIR / "librolibero_512.png", format="PNG")
    print(f"✓  {ICONS_DIR / 'librolibero_512.png'}  (prévia 512×512)")

    build_ico(base_png, ICONS_DIR / "librolibero.ico")
    build_icns(base_png, ICONS_DIR / "librolibero.icns")

    base_png.unlink()  # remove PNG temporário
    print(f"\nPronto! Arquivos em: {ICONS_DIR}")
