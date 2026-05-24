#!/usr/bin/env bash
# =============================================================================
# build.sh — Empacotamento do librolibero para macOS / Linux
#
# Uso (a partir da raiz do projeto):
#   bash packaging/build.sh
#
# Pré-requisitos:
#   pip install pyinstaller Pillow
#
# Artefato gerado:
#   macOS → dist/librolibero.app    (arraste para /Applications)
#   Linux → dist/librolibero/       (execute dist/librolibero/librolibero)
# =============================================================================
set -euo pipefail

# ── Raiz do projeto ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

# ── Verificar dependências ─────────────────────────────────────────────────
echo "▶ Verificando dependências…"

for cmd in python pyinstaller; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "❌  '$cmd' não encontrado. Instale antes de continuar."
        exit 1
    fi
done

python -c "import PIL" 2>/dev/null || {
    echo "⚠️  Pillow não encontrado — instalando…"
    pip install Pillow
}

# ── Gerar ícones ───────────────────────────────────────────────────────────
echo ""
echo "▶ Gerando ícones…"
python packaging/make_icons.py

# ── Limpar builds anteriores ───────────────────────────────────────────────
echo ""
echo "▶ Limpando builds anteriores…"
rm -rf dist/librolibero dist/librolibero.app build/librolibero

# ── Executar PyInstaller ───────────────────────────────────────────────────
echo ""
echo "▶ Empacotando com PyInstaller…"
pyinstaller packaging/librolibero.spec --noconfirm

# ── Resultado ─────────────────────────────────────────────────────────────
echo ""
if [[ "$(uname)" == "Darwin" ]]; then
    if [[ -d "dist/librolibero.app" ]]; then
        echo "✅  dist/librolibero.app criado com sucesso."
        echo "    Para instalar: arraste librolibero.app para /Applications"
        echo "    Para testar:   open dist/librolibero.app"
    else
        echo "❌  Algo deu errado — dist/librolibero.app não encontrado."
        exit 1
    fi
else
    if [[ -f "dist/librolibero/librolibero" ]]; then
        echo "✅  dist/librolibero/librolibero criado com sucesso."
        echo "    Para testar: ./dist/librolibero/librolibero"
    else
        echo "❌  Algo deu errado — dist/librolibero/librolibero não encontrado."
        exit 1
    fi
fi
