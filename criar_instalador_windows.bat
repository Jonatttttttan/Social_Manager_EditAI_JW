@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === EditAI Videos JW 0.9.8.4 Beta 2 - Instalador Windows ===
if not exist "dist\PromptVideoAI\PromptVideoAI.exe" (
 echo ERRO: execute primeiro build_windows.bat
 pause
 exit /b 1
)
".venv\Scripts\python.exe" verificar_build.py
if errorlevel 1 (echo ERRO: build incompleto. & pause & exit /b 1)
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
 echo ERRO: Inno Setup 6 nao encontrado. Instale em https://jrsoftware.org/isdl.php
 pause
 exit /b 1
)
"%ISCC%" "installer.iss"
if errorlevel 1 (echo ERRO: compilacao do instalador falhou. & pause & exit /b 1)
if not exist "installer_output\EditAI-Videos-JW-0.9.8.4-beta2-social-manager-Setup.exe" (
 echo ERRO: instalador nao encontrado.
 pause
 exit /b 1
)
echo.
echo Instalador criado em installer_output\EditAI-Videos-JW-0.9.8.4-beta2-social-manager-Setup.exe
echo TESTE em Windows limpo antes de distribuir.
pause
