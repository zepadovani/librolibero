"""Utilitários de recursos para a GUI.

Funciona tanto em desenvolvimento quanto após empacotamento com PyInstaller
(os recursos ficam em sys._MEIPASS quando empacotados).
"""

import sys
from pathlib import Path


def get_icon_path(filename: str) -> str:
    """Retorna o caminho absoluto de um arquivo em librolibero/icon/.

    Em dev:       <raiz>/librolibero/icon/<filename>
    PyInstaller:  sys._MEIPASS/librolibero/icon/<filename>
    """
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / "librolibero" / "icon" / filename)
    # __file__ = librolibero/gui/resources.py → parent.parent = librolibero/
    return str(Path(__file__).parent.parent / "icon" / filename)


def make_logo_widget(height: int = 64):
    """QWidget centralizado com o logotipo SVG horizontal (librolibero.svg).

    A largura é calculada automaticamente a partir do viewBox do SVG.
    """
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import QHBoxLayout, QWidget

    svg_path = get_icon_path("librolibero.svg")

    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    svg = QSvgWidget(svg_path)
    vb = svg.renderer().viewBoxF()
    width = int(height * vb.width() / vb.height()) if vb.height() > 0 else height * 2
    svg.setFixedSize(width, height)

    layout.addStretch()
    layout.addWidget(svg)
    layout.addStretch()

    return container
