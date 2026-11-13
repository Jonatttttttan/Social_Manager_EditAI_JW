@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 (echo Falha ao criar ambiente Python 3.12 & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (echo Falha ao instalar dependencias & pause & exit /b 1)
.venv\Scripts\python.exe main.py
if errorlevel 1 (echo Aplicacao terminou com erro & pause & exit /b 1)
