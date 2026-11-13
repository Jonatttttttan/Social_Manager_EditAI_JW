@echo off
setlocal
cd /d "%~dp0"
set "EDITAI_LICENSE_SERVER=https://editai-license-server-jw.onrender.com"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 (echo Python 3.12 necessario. & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (echo Erro ao instalar dependencias. & pause & exit /b 1)
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 (echo Erro ao iniciar o editor. & pause & exit /b 1)
endlocal
