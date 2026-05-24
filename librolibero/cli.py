"""CLI do librolibero — argparse + lógica interativa de duplicatas"""

import argparse
import os
import sys
import logging

from send2trash import send2trash

from .config import get_config
from .scanner import scan_and_extract
from .metadata import resolve_metadata, resolve_metadata_from_filename
from .zotero_client import (
    get_client,
    import_file,
    STRATEGY_ASK,
    STRATEGY_SKIP,
    STRATEGY_IMPORT,
    STRATEGY_ATTACH,
)
from .report import setup_logging, print_summary


def _prompt_duplicate_strategy(filepath: str, duplicates: list[dict], global_strategy: list) -> str:
    """Pergunta ao usuário o que fazer com uma duplicata.

    global_strategy é uma lista de 1 elemento usada como referência mutável;
    se o usuário escolher 'para todos', atualiza o valor para evitar novas perguntas.
    """
    print()
    print(f"  Duplicata detectada: {os.path.basename(filepath)}")
    print(f"  Itens existentes no Zotero:")
    for item in duplicates:
        data = item.get("data", {})
        print(f"    [{item['key']}] {data.get('title', '(sem título)')} ({data.get('date', '')})")
    print()
    print("  O que deseja fazer?")
    print("    1) Ignorar este arquivo")
    print("    2) Criar novo item mesmo assim")
    print("    3) Anexar ao item existente (mais recente)")
    print("    4) Ignorar TODOS os próximos duplicados")
    print("    5) Criar novos itens para TODOS os próximos duplicados")
    print("    6) Anexar TODOS os próximos duplicados ao item existente")

    while True:
        choice = input("  Escolha [1-6]: ").strip()
        if choice == "1":
            return STRATEGY_SKIP
        if choice == "2":
            return STRATEGY_IMPORT
        if choice == "3":
            return STRATEGY_ATTACH
        if choice == "4":
            global_strategy[0] = STRATEGY_SKIP
            return STRATEGY_SKIP
        if choice == "5":
            global_strategy[0] = STRATEGY_IMPORT
            return STRATEGY_IMPORT
        if choice == "6":
            global_strategy[0] = STRATEGY_ATTACH
            return STRATEGY_ATTACH
        print("  Opção inválida, tente novamente.")


def run(args: argparse.Namespace) -> None:
    logger = setup_logging()
    cfg = get_config()

    directory = args.dir or cfg["config"]["directory"]
    extensions = cfg["config"]["extensions"]
    dry_run = args.dry_run
    zotmoov_mode = cfg["config"].get("zotmoov_mode", False)

    if dry_run:
        logger.info("[DRY-RUN] Nenhuma requisição POST será enviada ao Zotero.")
    if zotmoov_mode and args.trash_after_import:
        logger.warning("[ZOTMOOV] --trash-after-import ignorado: zotmoov_mode=true no config.toml. "
                       "O ZotMoov moverá os arquivos automaticamente.")

    logger.info(f"Rastreando: {os.path.abspath(directory)}")
    files = scan_and_extract(directory, extensions)
    logger.info(f"{len(files)} arquivo(s) encontrado(s).")

    zot = None if dry_run else get_client()

    results = []
    # Referência mutável para estratégia global de duplicatas (None = perguntar sempre)
    global_strategy = [None]

    for entry in files:
        filepath = entry["path"]
        isbn = entry["isbn"]
        source = entry["isbn_source"]
        filename = entry["filename"]

        logger.info(f"Processando: {filename}")

        if not isbn:
            logger.warning(f"  ISBN não encontrado — tentando metadados do nome do arquivo.")
            metadata = resolve_metadata_from_filename(filepath)
            if not metadata:
                logger.warning(f"  Sem metadados disponíveis — ignorado.")
                results.append({"status": "no_isbn", "filepath": filepath})
                continue
            logger.info(f"  ISBN ausente; metadados extraídos do nome: '{metadata['title']}'")

        logger.debug(f"  ISBN: {isbn} (via {source})")

        metadata = resolve_metadata(isbn) if isbn else None
        if not metadata:
            logger.warning(f"  Metadados não resolvidos via API{' para ISBN ' + isbn if isbn else ''} — usando nome do arquivo.")
            metadata = resolve_metadata_from_filename(filepath)
        if not metadata:
            logger.warning(f"  Sem metadados disponíveis — ignorado.")
            results.append({"status": "failed", "filepath": filepath, "error": "metadados não encontrados"})
            continue

        logger.info(f"  → {metadata['title']} ({metadata['year']})")

        if dry_run:
            results.append({"status": "created", "filepath": filepath})
            logger.info("  [DRY-RUN] Item seria criado.")
            continue

        # Determinar estratégia para duplicatas
        strategy = global_strategy[0] or STRATEGY_ASK

        result = import_file(zot, filepath, metadata, duplicate_strategy=strategy)

        if result["status"] == "duplicate_ask":
            strategy = _prompt_duplicate_strategy(filepath, result["duplicates"], global_strategy)
            result = import_file(zot, filepath, metadata, duplicate_strategy=strategy)

        results.append(result)

        if result["status"] == "created":
            logger.info(f"  Criado: {result['item_key']}")
        elif result["status"] == "attached":
            logger.info(f"  Anexado a: {result['item_key']}")
        elif result["status"] == "skipped":
            logger.info(f"  Ignorado (duplicata).")

        if args.trash_after_import and not zotmoov_mode and result["status"] in ("created", "attached"):
            send2trash(filepath)
            logger.info(f"  Movido para lixeira: {os.path.basename(filepath)}")

    print_summary(results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="librolibero",
        description="Importa PDFs/EPUBs da pasta books/ para o Zotero via ISBN.",
    )
    parser.add_argument(
        "--dir",
        metavar="PASTA",
        default=None,
        help="Pasta de origem dos arquivos (padrão: books/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simula o processo sem enviar requisições POST ao Zotero.",
    )
    parser.add_argument(
        "--trash-after-import",
        action="store_true",
        default=False,
        help="Move o arquivo local para a lixeira após importação bem-sucedida.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        run(args)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
        sys.exit(1)
