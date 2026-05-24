"""Tela de Configuração de Credenciais Zotero.

Componente: ConfigFrame
Sinal emitido: credentials_saved() — MainWindow usa para navegar ao ScannerFrame.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


class ConfigFrame(QWidget):
    """Formulário para inserir e salvar credenciais do Zotero."""

    credentials_saved = Signal()   # emitido após salvar com sucesso

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load_existing_credentials()

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

        # --- Bloco de ajuda ---
        root.addWidget(self._build_help_box())

        # --- Formulário de campos ---
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._id_input = QLineEdit()
        self._id_input.setPlaceholderText("Ex: 1234567")
        self._id_input.setToolTip("Número inteiro exibido em Settings > Feeds/API")

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("Ex: aBcDeFgH1234567890")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setToolTip("Chave gerada em Settings > Feeds/API com permissão de escrita")

        form_layout.addRow("Zotero User ID:", self._id_input)
        form_layout.addRow("Zotero API Key:", self._key_input)
        root.addWidget(form_frame)

        # --- Mensagem de status inline ---
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        root.addWidget(self._status_label)

        # --- Botão Salvar ---
        self._save_btn = QPushButton("Salvar credenciais")
        self._save_btn.setFixedHeight(36)
        self._save_btn.clicked.connect(self._on_save)
        root.addWidget(self._save_btn)

        root.addStretch()

    def _build_help_box(self) -> QFrame:
        """Cria painel explicativo com link para a página do Zotero."""
        box = QFrame()
        box.setFrameShape(QFrame.Shape.StyledPanel)
        box.setStyleSheet("background: #f5f5f5; border-radius: 6px; padding: 4px;")

        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        intro = QLabel(
            "Para conectar ao Zotero você precisa de duas informações, "
            "ambas disponíveis em "
            "<a href='https://www.zotero.org/settings/keys'>Settings › Feeds/API</a>:"
        )
        intro.setOpenExternalLinks(True)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        details = QLabel(
            "<ul>"
            "<li><b>User ID</b> — número exibido no topo da página "
            "(ex: <i>\"Your userID for use in API calls is <b>1234567</b>\"</i>).</li>"
            "<li><b>API Key</b> — clique em <i>\"Create new private key\"</i> e marque "
            "permissão de <b>escrita</b> (<i>Write</i>) na biblioteca pessoal.</li>"
            "</ul>"
        )
        details.setWordWrap(True)
        details.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(details)

        open_link_btn = QPushButton("Abrir página de configuração do Zotero ↗")
        open_link_btn.setFlat(True)
        open_link_btn.setStyleSheet("color: #0066cc; text-decoration: underline;")
        open_link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_link_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.zotero.org/settings/keys"))
        )
        layout.addWidget(open_link_btn)

        return box

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------

    def _load_existing_credentials(self) -> None:
        """Pré-preenche os campos se credenciais já existirem."""
        try:
            from librolibero.config import load_env
            creds = load_env()
            self._id_input.setText(creds.get("ZOTERO_ID", ""))
            self._key_input.setText(creds.get("zoteroKEY", ""))
        except Exception:
            pass  # arquivo ausente ou inválido — campos ficam em branco

    def _set_status(self, msg: str, color: str = "#333") -> None:
        self._status_label.setText(msg)
        self._status_label.setStyleSheet(f"color: {color};")

    def _on_save(self) -> None:
        """Valida os campos e grava as credenciais no .env."""
        zotero_id = self._id_input.text().strip()
        zotero_key = self._key_input.text().strip()

        if not zotero_id or not zotero_key:
            self._set_status("⚠ Preencha o User ID e a API Key antes de salvar.", "#b94a00")
            return

        if not zotero_id.isdigit():
            self._set_status("⚠ O User ID deve conter apenas números.", "#b94a00")
            return

        try:
            from librolibero.config import save_credentials
            save_credentials(zotero_id, zotero_key)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))
            return

        self._set_status("✓ Credenciais salvas com sucesso!", "#2a7a2a")
        self.credentials_saved.emit()
