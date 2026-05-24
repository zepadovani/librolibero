@echo off
REM =============================================================================
REM build.bat — Empacotamento do librolibero para Windows
REM
REM Uso (a partir da raiz do projeto):
REM   packaging\build.bat
REM
REM Pre-requisitos:
REM   pip install pyinstaller Pillow
REM
REM Artefato gerado:
REM   dist\librolibero\librolibero.exe
REM =============================================================================

setlocal enabledelayedexpansion

REM Ir para a raiz do projeto
cd /d "%~dp0.."

echo [1/4] Verificando dependencias...

where python >nul 2>&1
if errorlevel 1 (
    echo ERRO: python nao encontrado no PATH.
    exit /b 1
)

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERRO: pyinstaller nao encontrado. Execute: pip install pyinstaller
    exit /b 1
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo Pillow nao encontrado. Instalando...
    pip install Pillow
)

echo [2/4] Gerando icones...
python packaging\make_icons.py
if errorlevel 1 (
    echo ERRO ao gerar icones.
    exit /b 1
)

echo [3/4] Limpando builds anteriores...
if exist dist\librolibero   rmdir /s /q dist\librolibero
if exist build\librolibero  rmdir /s /q build\librolibero

echo [4/4] Empacotando com PyInstaller...
pyinstaller packaging\librolibero.spec --noconfirm
if errorlevel 1 (
    echo ERRO no PyInstaller.
    exit /b 1
)

echo.
if exist "dist\librolibero\librolibero.exe" (
    echo OK  dist\librolibero\librolibero.exe criado com sucesso.
    echo     Para testar: dist\librolibero\librolibero.exe
) else (
    echo ERRO: dist\librolibero\librolibero.exe nao encontrado.
    exit /b 1
)

endlocal
