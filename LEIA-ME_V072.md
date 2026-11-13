# PromptVideo AI v0.7.2 — Progresso por vídeo

Esta versão mantém a interface e as funcionalidades da v0.7.1 e acrescenta barras de progresso para a edição individual e para cada item da fila, além do progresso geral do lote.

## Como usar

1. Extraia em pasta nova e mantenha a v0.7.1 como backup.
2. Configure `ffmpeg.exe` e `ffprobe.exe` na pasta `bin` ou no PATH.
3. Execute `run_windows.bat`.
4. Em **Editar um vídeo**, analise e confirme uma edição: acompanhe a barra do vídeo.
5. Em **Editar vários vídeos**, selecione 2 ou mais MP4: acompanhe uma barra por vídeo e o total da fila.

## Precisão dos indicadores

O percentual indica **etapas concluídas**, não quadros de vídeo codificados em tempo real. A codificação de um trecho, a análise de silêncio e a transcrição Whisper podem levar vários minutos sem alterar o percentual. Durante essas operações a etapa exibida informa o trabalho em curso. Não há estimativa de tempo restante. A fila é sequencial, e falhas individuais aparecem em vermelho sem interromper os outros vídeos.

## Testes

Testes unitários existentes executados no ambiente de desenvolvimento. A execução real com Gradio, FFmpeg e Whisper no Windows precisa ser validada pelo usuário.
