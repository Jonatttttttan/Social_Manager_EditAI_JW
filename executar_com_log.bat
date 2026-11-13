@echo off
setlocal
cd /d "%~dp0"
if not exist "dist\PromptVideoAI\PromptVideoAI.exe" (echo EXE nao encontrado. Rode build_windows.bat & pause & exit /b 1)
cd dist\PromptVideoAI
PromptVideoAI.exe > "%USERPROFILE%\Desktop\PromptVideoAI_erro.txt" 2>&1
echo Codigo de saida: %ERRORLEVEL%
echo Log salvo em: %USERPROFILE%\Desktop\PromptVideoAI_erro.txt
pause
