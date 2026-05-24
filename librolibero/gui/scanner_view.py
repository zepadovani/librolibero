"""Tela de Seleção de Diretório.

Componente: ScannerFrame
Sinal emitido: scan_requested(path: str, recursive: bool) — MainWindow usa para iniciar e navegar ao ProgressFrame.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QFrame, QFileDialog,
)
from PySide6.QtCore import Signal, Qt


class ScannerFrame(QWidget):
    """Formulário para escolher pasta e opções de varredura."""

    scan_requested = Signal(str, bool)  # (caminho, recursivo)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(20)

        # --- Logo ---
        from librolibero.gui.resources import make_logo_widget
        root.addWidget(make_logo_widget(height=64))

        # --- Bloco informativo ---
        root.addWidget(self._build_info_box())

        # --- Seletor de pasta ---
        root.addWidget(self._build_path_selector())

        # --- Checkbox subpastas ---
        self._recursive_check = QCheckBox("Vasculhar subpastas")
        self._recursive_check.setChecked(True)
        self._recursive_check.setToolTip(
            "Quando ativado, procura livros também em todas as subpastas da pasta escolhida."
        )
        root.addWidget(self._recursive_check)

        # --- Botão Iniciar ---
        self._start_btn = QPushButton("Iniciar varredura")
        self._start_btn.setFixedHeight(36)
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start)
        root.addWidget(self._start_btn)

        root.addStretch()

    def _build_info_box(self) -> QFrame:
        box = QFrame()
        box.setFrameShape(QFrame.Shape.StyledPanel)
        box.setStyleSheet("background: #f5f5f5; border-radius: 6px; padding: 4px;")

        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 12, 16, 12)

        info = QLabel(
            "Escolha a pasta onde seus livros estão armazenados. "
            "O librolibero irá procurar arquivos <b>.pdf</b>, <b>.epub</b>, "
            "<b>.mobi</b> e <b>.azw3</b> e enviá-los ao Zotero."
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)

        return box

    def _build_path_selector(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self._path_field = QLineEdit()
        self._path_field.setPlaceholderText("Nenhuma pasta selecionada")
        self._path_field.setReadOnly(True)
        row.addWidget(self._path_field, stretch=1)

        choose_btn = QPushButton("Escolher Pasta…")
        choose_btn.setFixedHeight(32)
        choose_btn.clicked.connect(self._on_choose_folder)
        row.addWidget(choose_btn)

        return container

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------

    def _on_choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecionar pasta de livros",
            self._path_field.text() or "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._path_field.setText(folder)
            self._start_btn.setEnabled(True)

    def _on_start(self) -> None:
        path = self._path_field.text().strip()
        recursive = self._recursive_check.isChecked()
        if path:
            self.scan_requested.emit(path, recursive)
