"""Tela de Progresso da Varredura.

Componente: ProgressFrame
Recebe: start_scan(path, recursive) chamado pelo MainWindow antes de exibir a tela.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QTextEdit, QPushButton, QHBoxLayout, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor


class ProgressFrame(QWidget):
    """Exibe barra de progresso e log em tempo real durante a importação."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 32, 40, 32)
        root.setSpacing(16)

        # --- Título ---
        title = QLabel("Importando para o Zotero…")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        self._title = title

        # --- Status resumido ---
        self._status_label = QLabel("Aguardando início…")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._status_label)

        # --- Barra de progresso ---
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        root.addWidget(self._progress_bar)

        # --- Log box ---
        self._log_box = QTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setFontFamily("Menlo, Consolas, monospace")
        self._log_box.setMinimumHeight(200)
        root.addWidget(self._log_box, stretch=1)

        # --- Botões ---
        btn_row = QHBoxLayout()
        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addStretch()
        btn_row.addWidget(self._cancel_btn)
        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def start_scan(self, path: str, recursive: bool) -> None:
        """Inicializa e dispara o worker. Chamado pelo MainWindow."""
        from librolibero.gui.worker import ScanWorker

        # Para worker anterior se ainda rodando
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait()

        # Reset da UI
        self._log_box.clear()
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(0)   # modo indeterminado até sabermos o total
        self._status_label.setText("Iniciando…")
        self._title.setText("Importando para o Zotero…")
        self._cancel_btn.setEnabled(True)

        # Worker
        self._worker = ScanWorker(path, recursive, parent=self)
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.critical_error.connect(self._on_critical_error)
        self._worker.start()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _append_log(self, message: str) -> None:
        self._log_box.append(message)
        # Rola para o fim automaticamente
        self._log_box.moveCursor(QTextCursor.MoveOperation.End)

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)
            self._status_label.setText(f"Processando {current} de {total}…")

    def _on_finished(self, success: bool) -> None:
        self._cancel_btn.setEnabled(False)
        if success:
            self._title.setText("Importação concluída ✓")
            self._status_label.setText("Todos os arquivos foram processados.")
            self._progress_bar.setValue(self._progress_bar.maximum())
        else:
            self._title.setText("Erro durante a importação")
            self._status_label.setText("Ocorreu um erro. Veja o log acima.")

    def _on_critical_error(self, title: str, detail: str) -> None:
        """Exibe QMessageBox modal para erros fatais (credenciais, rede)."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(title)
        msg.setInformativeText(detail)
        msg.exec()

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._cancel_btn.setEnabled(False)
            self._status_label.setText("Cancelando…")
