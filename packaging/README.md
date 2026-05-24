# Empacotamento — librolibero

## Estrutura

```
packaging/
  librolibero.spec      ← Spec PyInstaller (macOS + Windows)
  entrypoint_gui.py     ← Script de entrada para o PyInstaller
  make_icons.py         ← Gera .icns e .ico com Pillow
  build.sh              ← Script de build macOS/Linux
  build.bat             ← Script de build Windows
  icons/
    librolibero.icns    ← Gerado por make_icons.py
    librolibero.ico     ← Gerado por make_icons.py
    librolibero_512.png ← PNG de referência
  README.md             ← Este arquivo
```

## Pré-requisitos

```bash
pip install pyinstaller Pillow
```

> **macOS:** Para `.icns` de alta qualidade, o `iconutil` (incluso nos
> Xcode Command Line Tools) é usado automaticamente. Se não estiver disponível,
> `make_icons.py` gera um `.icns` básico sem dependências externas.

## Build

### macOS
```bash
bash packaging/build.sh
# → dist/librolibero.app
```

### Windows (PowerShell / cmd)
```bat
packaging\build.bat
# → dist\librolibero\librolibero.exe
```

### Manual (qualquer OS)
```bash
# 1. Gerar ícones
python packaging/make_icons.py

# 2. Empacotar
pyinstaller packaging/librolibero.spec --noconfirm
```

## Artefatos gerados

| OS      | Caminho                             | Como usar                          |
|---------|-------------------------------------|------------------------------------|
| macOS   | `dist/librolibero.app`              | Arraste para `/Applications`       |
| Windows | `dist/librolibero/librolibero.exe`  | Execute direto ou crie atalho      |
| Linux   | `dist/librolibero/librolibero`      | `./dist/librolibero/librolibero`   |

## Testar sem empacotar (desenvolvimento)

```bash
# Ativa o env com PySide6
pip install PySide6  # se necessário

python packaging/entrypoint_gui.py
# ou
python -m librolibero.gui.app
```

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'fitz'` | PyMuPDF não empacotado | Verifique `hiddenimports` no spec |
| App abre e fecha imediatamente | Exceção na inicialização | Execute com `console=True` no spec para ver o traceback |
| Ícone não aparece no macOS | `.icns` ausente ou inválido | Rode `make_icons.py` novamente |
| App bloqueado pelo Gatekeeper (macOS) | App não assinado | `xattr -rd com.apple.quarantine dist/librolibero.app` |
