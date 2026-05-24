"""Carregamento e gravação de configurações do .nosync/.env e config.toml"""

import os
import sys
from dotenv import load_dotenv

# tomllib é stdlib no Python 3.11+; cai em tomli para versões anteriores
try:
    import tomllib          # type: ignore[import]
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


def _env_path() -> str:
    """Retorna o caminho absoluto do arquivo .nosync/.env."""
    return os.path.join(os.path.dirname(__file__), "..", ".nosync", ".env")


def has_credentials() -> bool:
    """Retorna True se ZOTERO_ID e zoteroKEY estão presentes no .env."""
    try:
        load_env()
        return True
    except (ValueError, FileNotFoundError):
        return False


def save_credentials(zotero_id: str, zotero_key: str) -> None:
    """Grava (ou sobrescreve) ZOTERO_ID e zoteroKEY em .nosync/.env.

    Cria o arquivo e o diretório pai se não existirem.
    Preserva outras variáveis já presentes no arquivo.
    """
    env_path = _env_path()
    os.makedirs(os.path.dirname(env_path), exist_ok=True)

    # Lê linhas existentes para preservar outras variáveis
    existing_lines: list[str] = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    # Remove entradas antigas das duas chaves para reescrever limpas
    keys_to_overwrite = {"ZOTERO_ID", "zoteroKEY"}
    filtered = [
        line for line in existing_lines
        if not any(line.startswith(f"{k}=") for k in keys_to_overwrite)
    ]

    filtered.append(f"ZOTERO_ID={zotero_id}\n")
    filtered.append(f"zoteroKEY={zotero_key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(filtered)

    # Atualiza os.environ imediatamente para a sessão atual
    os.environ["ZOTERO_ID"] = zotero_id
    os.environ["zoteroKEY"] = zotero_key


def load_env():
    """Carrega variáveis de .nosync/.env"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".nosync", ".env")
    load_dotenv(env_path)
    
    zotero_id = os.getenv("ZOTERO_ID")
    zotero_key = os.getenv("zoteroKEY")
    
    if not zotero_id or not zotero_key:
        raise ValueError("ZOTERO_ID e zoteroKEY não encontrados em .nosync/.env")
    
    return {"ZOTERO_ID": zotero_id, "zoteroKEY": zotero_key}

def load_config():
    """Carrega configurações gerais de config.toml"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.toml")
    
    # Configurações padrão
    defaults = {
        "directory": "books/",
        "extensions": [".pdf", ".epub", ".mobi", ".azw3"],
        "zotmoov_mode": True,   # True = ZotMoov gerencia os arquivos; desativa --trash-after-import
    }
    
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            user_config = tomllib.load(f)
        defaults.update(user_config)
    
    return defaults

def get_config():
    """Retorna configuração consolidada: env + config.toml"""
    env_vars = load_env()
    config = load_config()
    
    return {
        "env": env_vars,
        "config": config
    }
