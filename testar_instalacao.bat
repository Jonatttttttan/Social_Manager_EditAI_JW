@echo off
setlocal
set "APP=%LOCALAPPDATA%\Programs\EditAI Videos JW\PromptVideoAI.exe"
echo === Teste da instalacao EditAI Videos JW ===
if not exist "%APP%" (
 echo ERRO: aplicativo nao instalado no local padrao: "%APP%"
 echo Se voce escolheu outro diretorio, abra o EXE manualmente nesse diretorio.
 pause
 exit /b 1
)
echo Aplicativo encontrado. Abrindo para teste interativo...
echo Confira se a interface abre, se edita um video e se exporta MP4.
"%APP%"
echo.
echo O aplicativo encerrou. Se houve erro, copie a mensagem acima.
pause
