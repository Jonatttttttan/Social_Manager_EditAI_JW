@echo off
setlocal
cd /d "%~dp0"
echo === EditAI Videos JW v0.9.8.4-beta2-social-manager - Auditoria e testes ===
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=py -3.12")
%PY% auditoria_beta.py
if errorlevel 1 (echo FALHA na auditoria. & pause & exit /b 1)
%PY% -m pytest tests -v --tb=short
if errorlevel 1 (echo FALHA nos testes. & pause & exit /b 1)
echo Testes Python OK. Agora teste manualmente a interface, exportacao e instalacao.
pause
