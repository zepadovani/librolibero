"""Worker QThread — executa varredura + importação Zotero em background.

Sinais:
    progress(current, total) → atualiza QProgressBar
    log(message)             → adiciona linha ao LogBox
    finished(success)        → varredura concluída ou abortada
"""

import os
from PySide6.QtCore import QThread, Signal


class ScanWorker(QThread):
    progress       = Signal(int, int)   # (current, total)
    log            = Signal(str)        # mensagem de log
    finished       = Signal(bool)       # True = sucesso, False = erro fatal
    critical_error = Signal(str, str)   # (título, detalhe) — para QMessageBox

    def __init__(self, path: str, recursive: bool, parent=None) -> None:
        super().__init__(parent)
        self._path      = path
        self._recursive = recursive
        self._abort     = False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def abort(self) -> None:
        """Sinaliza ao loop de processamento que deve parar na próxima iteração."""
        self._abort = True

    # ------------------------------------------------------------------
    # Thread principal
    # ------------------------------------------------------------------

    def run(self) -> None:
        try:
            self._do_scan()
            self.finished.emit(True)
        except Exception as exc:
            self.log.emit(f"Erro fatal: {exc}")
            self.finished.emit(False)

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _collect_files(self, extensions: list[str]) -> list[str]:
        ext_set = {e.lower() for e in extensions}
        files: list[str] = []

        if self._recursive:
            for root, _, names in os.walk(self._path):
                for name in names:
                    if os.path.splitext(name)[1].lower() in ext_set:
                        files.append(os.path.join(root, name))
        else:
            with os.scandir(self._path) as it:
                for entry in it:
                    if entry.is_file() and os.path.splitext(entry.name)[1].lower() in ext_set:
                        files.append(entry.path)

        return sorted(files)

    def _do_scan(self) -> None:
        # --- Configuração ---
        from librolibero.config import load_config
        config    = load_config()
        extensions = config.get("extensions", [".pdf", ".epub", ".mobi", ".azw3"])

        # --- Coleta de arquivos ---
        files = self._collect_files(extensions)
        total = len(files)
        self.log.emit(f"Encontrados {total} arquivo(s) em '{self._path}'.")
        self.progress.emit(0, total)

        if total == 0:
            return

        # --- Cliente Zotero ---
        from librolibero.zotero_client import get_client, import_file
        try:
            zot = get_client()
        except Exception as exc:
            self.critical_error.emit(
                "Credenciais inválidas",
                f"Não foi possível conectar ao Zotero.\n\nVerifique o User ID e a API Key nas configurações.\n\nDetalhe: {exc}",
            )
            raise

        # --- Metadados e importação ---
        from librolibero.scanner import extract_isbn_from_filename, extract_isbn_from_content
        from librolibero.metadata import resolve_metadata, resolve_metadata_from_filename

        for i, filepath in enumerate(files, 1):
            if self._abort:
                self.log.emit("⏹ Varredura interrompida pelo usuário.")
                return

            filename = os.path.basename(filepath)
            self.log.emit(f"[{i}/{total}] {filename}")
            self.progress.emit(i, total)

            # ISBN
            isbn = extract_isbn_from_filename(filepath) or extract_isbn_from_content(filepath)
            meta = None

            # 1. Tentar buscar metadados via API se tivermos o ISBN
            if isbn:
                try:
                    meta = resolve_metadata(isbn)
                except OSError as exc:
                    # Falha de rede na consulta de metadados — emite pop-up e aborta
                    self.critical_error.emit(
                        "Sem conexão com a internet",
                        f"Falha ao buscar metadados. Verifique sua conexão.\n\nDetalhe: {exc}",
                    )
                    raise
                except Exception as exc:
                    self.log.emit(f"  → Erro na API de metadados: {exc}")

            # 2. Fallback: tentar extrair metadados do nome do arquivo se a API falhar ou não houver ISBN
            if not meta:
                self.log.emit("  → Metadados não resolvidos via API — tentando extrair do nome do arquivo.")
                meta = resolve_metadata_from_filename(filepath)

            # 3. Se ainda assim não houver metadados, ignora o arquivo
            if not meta:
                self.log.emit("  → Metadados não encontrados, ignorando.")
                continue

            # Importar no Zotero
            try:
                result = import_file(zot, filepath, meta, duplicate_strategy="skip")
                status = result["status"]
                if status == "created":
                    self.log.emit("  ✓ Adicionado ao Zotero.")
                elif status == "skipped":
                    self.log.emit("  → Duplicata detectada, ignorado.")
                elif status == "attached":
                    self.log.emit("  → Anexado a item existente.")
            except OSError as exc:
                self.critical_error.emit(
                    "Sem conexão com a internet",
                    f"Falha ao importar para o Zotero. Verifique sua conexão.\n\nDetalhe: {exc}",
                )
                raise
            except Exception as exc:
                self.log.emit(f"  ✗ Erro ao importar: {exc}")
