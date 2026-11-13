# PromptVideo AI v0.8.2 — auditoria do empacotamento

## O que foi corrigido

- Build por arquivo `.spec` versionado, sem depender de opcoes temporarias da linha de comando.
- Coleta de recursos e imports ocultos de Gradio, Gradio Client, safehttpx, groovy, Whisper, CTranslate2, PyAV, tokenizers, Hugging Face Hub e ONNX Runtime.
- Inclusao explicita dos arquivos `safehttpx/version.txt` e `groovy/version.txt`.
- Verificacao automatica dos dois arquivos e dos binarios FFmpeg apos compilacao.
- Script `executar_com_log.bat` para capturar erros de inicializacao.

## Como utilizar

1. Extraia o ZIP em pasta NOVA. Copie `ffmpeg.exe` e `ffprobe.exe` para `bin`.
2. Execute `build_windows.bat` com internet para instalar dependencias e compilar no Windows 64 bits.
3. Confira se o script de verificacao terminou sem erros.
4. Execute `dist\PromptVideoAI\PromptVideoAI.exe`. Se fechar, use `executar_com_log.bat` e envie o log.
5. Teste interface, edicao MP4/MOV, audio, legendas, fila e barra de progresso.
6. Somente depois execute `criar_instalador_windows.bat` (requer Inno Setup 6).

## Limites da auditoria

Esta auditoria cobre falhas conhecidas e dependencias de empacotamento, mas NAO garante ausencia de todos os erros. A compilacao do executavel e os testes de integracao no Windows precisam ser feitos no seu PC. `faster-whisper` pode baixar modelos na primeira execucao (internet necessaria), a depender do cache; antivirus, codecs, permissao de escrita e drivers tambem podem afetar o resultado. O ZIP contem codigo e scripts, nao um EXE compilado. Verifique licencas do FFmpeg e dependencias antes de distribuicao comercial.
