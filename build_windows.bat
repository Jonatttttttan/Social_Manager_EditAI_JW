@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === EditAI Videos JW v0.9.8.4 Beta 2 - Build Windows ===
where py >nul 2>nul
if errorlevel 1 (echo ERRO: Python Launcher nao encontrado. & pause & exit /b 1)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 (echo ERRO: instale Python 3.12. & pause & exit /b 1)
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -c "import sys; assert sys.version_info[:2] == (3,12), 'Use Python 3.12'"
if errorlevel 1 (echo ERRO: use um ambiente Python 3.12 novo. & pause & exit /b 1)
if not exist "bin\ffmpeg.exe" (echo ERRO: falta bin\ffmpeg.exe & pause & exit /b 1)
if not exist "bin\ffprobe.exe" (echo ERRO: falta bin\ffprobe.exe & pause & exit /b 1)
"%PY%" -m pip install -r requirements.txt "pyinstaller>=6,<7" "pytest==9.2.0"
if errorlevel 1 (echo ERRO: instalacao de dependencias falhou. & pause & exit /b 1)
"%PY%" -m pytest tests -v --tb=short
if errorlevel 1 (echo ERRO: testes falharam. & pause & exit /b 1)
"%PY%" -m PyInstaller --noconfirm --clean PromptVideoAI.spec
if errorlevel 1 (echo ERRO: compilacao falhou. & pause & exit /b 1)
"%PY%" verificar_build.py
if errorlevel 1 (echo ERRO: verificacao do build falhou. & pause & exit /b 1)
echo.
echo Build criado. TESTE dist\PromptVideoAI\PromptVideoAI.exe antes do instalador.
pause
