"""Resolução de metadados bibliográficos a partir de ISBN em cascata"""

import os
import re
import requests

_RE_YEAR = re.compile(r'\b(1[5-9]\d\d|20\d\d)\b')
_RE_ISBN_SEG = re.compile(r'^isbn\d*\s+\d+', re.IGNORECASE)
_RE_HASH_SEG = re.compile(r'^[0-9a-f]{16,}$', re.IGNORECASE)

# --- 3.1 Busca primária via isbnlib merge ---

def _fetch_isbnlib(isbn: str, service: str) -> dict | None:
    """Consulta isbnlib com o serviço indicado. Retorna dict bruto ou None."""
    try:
        import isbnlib
        data = isbnlib.meta(isbn, service=service)
        if data and data.get("Title"):
            return data
    except Exception:
        pass
    return None


# --- 3.2 Fallback direto à Open Library ---

def _fetch_open_library(isbn: str) -> dict | None:
    """Consulta direta à API REST da Open Library. Retorna dict normalizado ou None."""
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        key = f"ISBN:{isbn}"
        if key not in data:
            return None
        book = data[key]
        authors = [a.get("name", "") for a in book.get("authors", [])]
        publishers = book.get("publishers", [{}])
        publisher = publishers[0].get("name", "") if publishers else ""
        publish_date = book.get("publish_date", "")
        year = publish_date[-4:] if len(publish_date) >= 4 else publish_date
        return {
            "Title": book.get("title", ""),
            "Year": year,
            "Publisher": publisher,
            "Authors": authors,
            "ISBN-13": isbn,
        }
    except Exception:
        pass
    return None


# --- 3.3 Normalização ---

def _normalize(raw: dict, isbn: str) -> dict:
    """Normaliza dict de qualquer fonte para estrutura uniforme.

    Retorna:
        {
            "title": str,
            "year": str,
            "publisher": str,
            "authors": list[str],   # ["Sobrenome, Nome", ...]
            "isbn": str
        }
    """
    # isbnlib retorna 'Authors' como lista de strings "Sobrenome, Nome"
    # Open Library retorna 'Authors' como lista de strings "Nome Sobrenome"
    authors = raw.get("Authors") or raw.get("authors") or []
    if not isinstance(authors, list):
        authors = [authors]

    return {
        "title": raw.get("Title") or raw.get("title") or "",
        "year": str(raw.get("Year") or raw.get("year") or ""),
        "publisher": raw.get("Publisher") or raw.get("publisher") or "",
        "authors": [a for a in authors if a],
        "isbn": isbn,
    }


# --- 3.2 Fallback Google Books ---

def _fetch_google_books(isbn: str) -> dict | None:
    """Consulta direta à API pública do Google Books. Retorna dict normalizado ou None."""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("totalItems", 0) == 0:
            return None
        info = data["items"][0].get("volumeInfo", {})
        published = info.get("publishedDate", "")
        year = published[:4] if len(published) >= 4 else published
        publishers = info.get("publisher", "")
        return {
            "Title": info.get("title", ""),
            "Year": year,
            "Publisher": publishers,
            "Authors": info.get("authors", []),
            "ISBN-13": isbn,
        }
    except Exception:
        pass
    return None


# --- API pública ---

def resolve_metadata(isbn: str) -> dict | None:
    """Resolve metadados para um ISBN usando cascata de serviços.

    Ordem:
    1. isbnlib merge  (WorldCat + Google Books)
    2. isbnlib openl  (Open Library via isbnlib)
    3. Open Library   (chamada REST direta)
    4. Google Books   (API pública REST)

    Retorna dict normalizado ou None se todos falharem.
    """
    for service in ("merge", "openl"):
        raw = _fetch_isbnlib(isbn, service)
        if raw:
            return _normalize(raw, isbn)

    raw = _fetch_open_library(isbn)
    if raw:
        return _normalize(raw, isbn)

    raw = _fetch_google_books(isbn)
    if raw:
        return _normalize(raw, isbn)

    return None


# --- Fallback via nome do arquivo ---

def resolve_metadata_from_filename(filepath: str) -> dict | None:
    """Extrai metadados do padrão de nome 'Título -- Autor -- Ano -- Editora -- ...'
    usado em arquivos com nomes estruturados. Retorna dict normalizado ou None se não for possível.
    """
    stem = os.path.splitext(os.path.basename(filepath))[0]
    segments = [s.strip() for s in stem.split(" -- ")]

    # Remover segmentos de hash e sufixos genéricos
    segments = [
        s for s in segments
        if not _RE_HASH_SEG.match(s) and "anna" not in s.lower()
    ]

    if not segments:
        return None

    # Segmento 0: título — troca underscores por dois-pontos
    title = re.sub(r'_', ':', segments[0]).strip(": ")

    # Segmento 1: autores — separados por ";" ou única string
    authors = []
    if len(segments) > 1:
        raw_authors = re.sub(r'^(?:par|by)\s+', '', segments[1], flags=re.IGNORECASE)
        authors = [a.strip() for a in re.split(r'\s*;\s*', raw_authors) if a.strip()]

    # Restantes: extrair ano e editora
    year = ""
    publisher = ""
    for seg in segments[2:]:
        if _RE_ISBN_SEG.match(seg):
            continue
        m = _RE_YEAR.search(seg)
        if m and not year:
            year = m.group(1)
            # Tentar publisher no mesmo segmento (antes do ano)
            candidate = seg[: m.start()].strip(" ,")
            if candidate and not publisher:
                publisher = candidate
            continue
        if seg and not publisher:
            publisher = seg

    if not title:
        return None

    return {
        "title": title,
        "year": year,
        "publisher": publisher,
        "authors": authors,
        "isbn": "",
    }
