"""Integração com a API do Zotero: criação de itens, anexos e gestão de duplicatas"""

import os
import mimetypes
from pyzotero import zotero

from .config import load_env

# Estratégias para duplicatas
STRATEGY_ASK = "ask"          # perguntar ao usuário (tratado pelo CLI)
STRATEGY_SKIP = "skip"        # ignorar o arquivo
STRATEGY_IMPORT = "import"    # importar mesmo assim (novo item)
STRATEGY_ATTACH = "attach"    # anexar ao item existente


# --- 4.1 Cliente e template ---

def get_client() -> zotero.Zotero:
    """Instancia e retorna cliente Zotero usando credenciais do .env."""
    env = load_env()
    return zotero.Zotero(env["ZOTERO_ID"], "user", env["zoteroKEY"])


def _parse_author(name: str) -> dict:
    """Converte string de autor para dict de creator do Zotero.

    Aceita 'Sobrenome, Nome' ou 'Nome Sobrenome'.
    """
    if "," in name:
        parts = name.split(",", 1)
        return {"creatorType": "author", "lastName": parts[0].strip(), "firstName": parts[1].strip()}
    parts = name.rsplit(" ", 1)
    if len(parts) == 2:
        return {"creatorType": "author", "lastName": parts[1].strip(), "firstName": parts[0].strip()}
    return {"creatorType": "author", "lastName": name.strip(), "firstName": ""}


def build_book_template(zot: zotero.Zotero, metadata: dict) -> dict:
    """Constrói template de item 'book' a partir de metadados normalizados."""
    template = zot.item_template("book")
    template["title"] = metadata.get("title", "")
    template["date"] = metadata.get("year", "")
    template["publisher"] = metadata.get("publisher", "")
    template["ISBN"] = metadata.get("isbn", "")
    template["creators"] = [_parse_author(a) for a in metadata.get("authors", [])]
    return template


# --- 4.2 Criação de item ---

def create_item(zot: zotero.Zotero, metadata: dict) -> str:
    """Cria item do tipo book no Zotero. Retorna a chave (key) do item criado."""
    template = build_book_template(zot, metadata)
    response = zot.create_items([template])
    # pyzotero retorna {"successful": {"0": {item}}, "failed": {...}}
    successful = response.get("successful", {})
    if not successful:
        failed = response.get("failed", {})
        raise RuntimeError(f"Falha ao criar item no Zotero: {failed}")
    item = list(successful.values())[0]
    return item["key"]


# --- 4.3 Anexo linked_file ---

def attach_linked_file(zot: zotero.Zotero, parent_key: str, filepath: str) -> None:
    """Cria anexo do tipo linked_file vinculado ao item pai."""
    abs_path = os.path.abspath(filepath)
    filename = os.path.basename(filepath)
    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = "application/octet-stream"

    template = zot.item_template("attachment", linkmode="linked_file")
    template["title"] = filename
    template["path"] = abs_path
    template["contentType"] = content_type

    zot.create_items([template], parentid=parent_key)


# --- Detecção de duplicatas ---

def find_existing_by_isbn(zot: zotero.Zotero, isbn: str) -> list[dict]:
    """Busca itens existentes no Zotero com o ISBN fornecido.

    Retorna lista de itens encontrados (pode ser vazia).
    """
    results = zot.items(q=isbn, itemType="book", limit=10)
    isbn_clean = isbn.replace("-", "").replace(" ", "")
    matches = []
    for item in results:
        data = item.get("data", {})
        existing_isbn = data.get("ISBN", "").replace("-", "").replace(" ", "")
        if isbn_clean in existing_isbn or existing_isbn in isbn_clean:
            matches.append(item)
    return matches


# --- API pública de importação ---

def import_file(
    zot: zotero.Zotero,
    filepath: str,
    metadata: dict,
    duplicate_strategy: str = STRATEGY_ASK,
) -> dict:
    """Importa um arquivo para o Zotero com a estratégia de duplicata indicada.

    Parâmetros:
        zot: cliente Zotero
        filepath: caminho absoluto do arquivo
        metadata: dict normalizado da Fase 3
        duplicate_strategy: "ask" | "skip" | "import" | "attach"

    Retorna dict com:
        {
            "status": "created" | "attached" | "skipped" | "duplicate_ask",
            "item_key": str | None,
            "duplicates": list[dict],   # itens existentes, se houver
            "filepath": str
        }
    """
    isbn = metadata.get("isbn", "")
    duplicates = find_existing_by_isbn(zot, isbn) if isbn else []

    if duplicates:
        if duplicate_strategy == STRATEGY_SKIP:
            return {"status": "skipped", "item_key": None, "duplicates": duplicates, "filepath": filepath}

        if duplicate_strategy == STRATEGY_ATTACH:
            existing_key = duplicates[0]["key"]
            attach_linked_file(zot, existing_key, filepath)
            return {"status": "attached", "item_key": existing_key, "duplicates": duplicates, "filepath": filepath}

        if duplicate_strategy == STRATEGY_ASK:
            # Sinaliza para o chamador (CLI) que precisa perguntar ao usuário
            return {"status": "duplicate_ask", "item_key": None, "duplicates": duplicates, "filepath": filepath}

        # STRATEGY_IMPORT: continua para criar novo item normalmente

    item_key = create_item(zot, metadata)
    attach_linked_file(zot, item_key, filepath)
    return {"status": "created", "item_key": item_key, "duplicates": duplicates, "filepath": filepath}
