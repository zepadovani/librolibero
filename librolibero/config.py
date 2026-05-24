"""Carregamento de configurações do .nosync/.env e config.toml"""

import os
import sys
import tomli
from dotenv import load_dotenv

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
            user_config = tomli.load(f)
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
