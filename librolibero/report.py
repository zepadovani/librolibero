"""Logging e relatório final de importação"""

import logging
import os
from datetime import date


def setup_logging() -> logging.Logger:
    """Configura logger com saída para console e arquivo logs/import_YYYY-MM-DD.log."""
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(logs_dir, f"import_{date.today().isoformat()}.log")

    logger = logging.getLogger("librolibero")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


def print_summary(results: list[dict]) -> None:
    """Imprime e registra resumo final da importação."""
    logger = logging.getLogger("librolibero")

    created  = [r for r in results if r["status"] == "created"]
    attached = [r for r in results if r["status"] == "attached"]
    skipped  = [r for r in results if r["status"] == "skipped"]
    failed   = [r for r in results if r["status"] == "failed"]
    no_isbn  = [r for r in results if r["status"] == "no_isbn"]

    lines = [
        "",
        "=" * 50,
        "  RESUMO DA IMPORTAÇÃO",
        "=" * 50,
        f"  Criados (novo item + anexo): {len(created)}",
        f"  Anexados a item existente:   {len(attached)}",
        f"  Ignorados (duplicata):       {len(skipped)}",
        f"  Sem ISBN detectado:          {len(no_isbn)}",
        f"  Falhas:                      {len(failed)}",
        f"  Total processados:           {len(results)}",
        "=" * 50,
    ]

    for line in lines:
        logger.info(line)

    if failed:
        logger.info("  Detalhes das falhas:")
        for r in failed:
            logger.info(f"    - {r['filepath']}: {r.get('error', '')}")

    if no_isbn:
        logger.info("  Arquivos sem ISBN:")
        for r in no_isbn:
            logger.info(f"    - {r['filepath']}")
