"""Rastreio de arquivos em books/ e extração de ISBN via nome ou conteúdo"""

import os
import re

# Regex para padrão explícito 'isbn13 XXXXXXXXXXXXX' nos nomes de arquivo
_RE_ISBN13_LABEL = re.compile(r'isbn13\s+(\d{13})', re.IGNORECASE)
# Regex genérico para ISBN-13 e ISBN-10 soltos no nome/texto
_RE_ISBN13 = re.compile(r'(?<!\d)(\d{13})(?!\d)')
_RE_ISBN10 = re.compile(r'(?<!\d)(\d{9}[\dXx])(?!\d)')


# --- 2.1 Rastreio de arquivos ---

def scan_directory(directory: str, extensions: list[str] | None = None) -> list[str]:
    """Retorna lista de caminhos absolutos dos arquivos com extensões permitidas."""
    if extensions is None:
        extensions = [".pdf", ".epub"]
    ext_set = {e.lower() for e in extensions}
    found = []
    for entry in os.scandir(directory):
        if entry.is_file():
            _, ext = os.path.splitext(entry.name)
            if ext.lower() in ext_set:
                found.append(os.path.abspath(entry.path))
    return sorted(found)


# --- 2.2 Extração via nome do arquivo ---

def extract_isbn_from_filename(filepath: str) -> str | None:
    """Tenta extrair ISBN do nome do arquivo.
    
    Prioridade:
    1. Padrão explícito 'isbn13 XXXXXXXXXXXXX'
    2. ISBN-13 genérico (13 dígitos consecutivos)
    3. ISBN-10 genérico (9 dígitos + dígito de controle X/x/0-9)
    """
    name = os.path.basename(filepath)
    
    m = _RE_ISBN13_LABEL.search(name)
    if m:
        return m.group(1)
    
    m = _RE_ISBN13.search(name)
    if m:
        return m.group(1)
    
    m = _RE_ISBN10.search(name)
    if m:
        return m.group(1).upper()
    
    return None


# Padrões a remover na limpeza de nome para busca reversa
_RE_HASH = re.compile(r'\b[0-9a-f]{16,}\b', re.IGNORECASE)
_RE_NOISE = re.compile(
    r"Anna[''`]?s?\s*Archive|Anna Archive|--+|\s{2,}",
    re.IGNORECASE
)


def extract_search_terms_from_filename(filepath: str) -> str | None:
    """Retorna termos de busca limpos quando nenhum ISBN foi encontrado no nome.

    Remove hashes MD5/SHA, sufixos comuns e separadores '--'.
    Retorna None se o resultado limpo for vazio.
    """
    stem = os.path.splitext(os.path.basename(filepath))[0]
    stem = _RE_HASH.sub('', stem)
    stem = _RE_NOISE.sub(' ', stem)
    terms = stem.strip(' -').strip()
    return terms if terms else None


# --- 2.3 Fallback: extração via conteúdo ---

def _extract_isbn_from_text(text: str) -> str | None:
    """Tenta localizar ISBN em um bloco de texto."""
    m = _RE_ISBN13_LABEL.search(text)
    if m:
        return m.group(1)
    m = _RE_ISBN13.search(text)
    if m:
        return m.group(1)
    m = _RE_ISBN10.search(text)
    if m:
        return m.group(1).upper()
    return None


def _extract_isbn_from_pdf(filepath: str) -> str | None:
    """Lê as primeiras 5 páginas de um PDF via pymupdf em busca de ISBN."""
    try:
        import fitz  # pymupdf
    except ImportError:
        return None

    try:
        doc = fitz.open(filepath)
        pages_to_check = min(5, len(doc))
        for i in range(pages_to_check):
            text = doc[i].get_text()
            isbn = _extract_isbn_from_text(text)
            if isbn:
                doc.close()
                return isbn
        doc.close()
    except Exception:
        pass
    return None


def _extract_isbn_from_epub(filepath: str) -> str | None:
    """Lê metadados OPF de um EPUB via ebooklib em busca de ISBN."""
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        return None

    try:
        book = epub.read_epub(filepath, options={"ignore_ncx": True})
        
        # Verificar metadados Dublin Core: identifier
        identifiers = book.get_metadata("DC", "identifier")
        for value, attrs in identifiers:
            isbn = _extract_isbn_from_text(str(value))
            if isbn:
                return isbn
        
        # Verificar título e outros campos como fallback textual
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content().decode("utf-8", errors="ignore")
            isbn = _extract_isbn_from_text(content)
            if isbn:
                return isbn
    except Exception:
        pass
    return None


def extract_isbn_from_content(filepath: str) -> str | None:
    """Fallback: extrai ISBN do conteúdo do arquivo (PDF ou EPUB)."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    if ext == ".pdf":
        return _extract_isbn_from_pdf(filepath)
    elif ext == ".epub":
        return _extract_isbn_from_epub(filepath)
    return None


# --- API pública ---

def scan_and_extract(directory: str, extensions: list[str] | None = None) -> list[dict]:
    """Rastreia o diretório e extrai ISBN de cada arquivo encontrado.
    
    Retorna lista de dicts:
        {
            "path": str,          # caminho absoluto
            "filename": str,      # nome do arquivo
            "isbn": str | None,   # ISBN extraído
            "isbn_source": str    # "filename" | "content" | "none"
        }
    """
    files = scan_directory(directory, extensions)
    results = []
    for filepath in files:
        isbn = extract_isbn_from_filename(filepath)
        source = "filename" if isbn else "none"

        if isbn is None:
            isbn = extract_isbn_from_content(filepath)
            source = "content" if isbn else "none"

        search_terms = None if isbn else extract_search_terms_from_filename(filepath)

        results.append({
            "path": filepath,
            "filename": os.path.basename(filepath),
            "isbn": isbn,
            "isbn_source": source,
            "search_terms": search_terms,
        })
    return results
