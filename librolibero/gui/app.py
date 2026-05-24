"""Janela principal do librolibero GUI.

Ponto de entrada: run_app()
Estrutura de navegação: QStackedWidget com views independentes.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt


APP_TITLE = "librolibero"
APP_MIN_WIDTH = 640
APP_MIN_HEIGHT = 480


class MainWindow(QMainWindow):
    """Janela raiz da aplicação.

    Usa QStackedWidget para alternar entre telas (Config, Scanner, Progress)
    sem destruí-las — cada view é adicionada uma vez e reutilizada.
    """

    # Índices das views no stack (adicionados na ordem abaixo)
    PAGE_CONFIG = 0
    PAGE_SCANNER = 1
    PAGE_PROGRESS = 2

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(APP_MIN_WIDTH, APP_MIN_HEIGHT)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._init_pages()
        self._navigate_to_start()

    # ------------------------------------------------------------------
    # Inicialização das páginas
    # ------------------------------------------------------------------

    def _init_pages(self) -> None:
        """Instancia e registra todas as views no stack.

        As views são importadas localmente para manter o escopo de contexto
        mínimo ao longo do desenvolvimento iterativo.
        """
        from librolibero.gui.config_view import ConfigFrame

        # PAGE_CONFIG (índice 0)
        self._config_view = ConfigFrame()
        self._config_view.credentials_saved.connect(
            lambda: self.show_page(self.PAGE_SCANNER)
        )
        self._stack.addWidget(self._config_view)

        # PAGE_SCANNER (índice 1)
        from librolibero.gui.scanner_view import ScannerFrame
        self._scanner_view = ScannerFrame()
        self._scanner_view.scan_requested.connect(self._on_scan_requested)
        self._stack.addWidget(self._scanner_view)

        # PAGE_PROGRESS (índice 2)
        from librolibero.gui.progress_view import ProgressFrame
        self._progress_view = ProgressFrame()
        self._stack.addWidget(self._progress_view)

    # ------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------

    def show_page(self, page_index: int) -> None:
        """Exibe a view indicada pelo índice (PAGE_* constantes)."""
        self._stack.setCurrentIndex(page_index)

    def _on_scan_requested(self, path: str, recursive: bool) -> None:
        """Recebe parâmetros do ScannerFrame, inicia worker e exibe ProgressFrame."""
        self._progress_view.start_scan(path, recursive)
        self.show_page(self.PAGE_PROGRESS)

    def _navigate_to_start(self) -> None:
        """Abre Scanner se há credenciais salvas; caso contrário, abre Config."""
        from librolibero.config import has_credentials
        if has_credentials():
            self.show_page(self.PAGE_SCANNER)
        else:
            self.show_page(self.PAGE_CONFIG)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def run_app() -> None:
    """Inicializa e executa o loop de eventos Qt."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
