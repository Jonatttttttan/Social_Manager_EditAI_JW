# PromptVideo AI v0.5 — Legendas automáticas

Baseado na v0.4. Legendas **opcionais**, com estilos **Tradicional** e **Dinâmica**.

## Instalação no Windows

1. Preserve a v0.4 como backup.
2. Extraia este ZIP em uma pasta nova.
3. Copie `ffmpeg.exe` e `ffprobe.exe` para `bin/`, se não estiverem no PATH.
4. Execute `run_windows.bat`.
5. Carregue um vídeo, digite uma instrução de edição e clique em **Analisar vídeo**.
6. Revise os cortes, marque **Adicionar legendas ao vídeo final**, escolha o estilo e clique em **Aplicar edição aprovada**.
7. Baixe o MP4 com legendas e, opcionalmente, o arquivo SRT editável.

## Observações

- As legendas são geradas **depois dos cortes e da melhoria de áudio**, para manter sincronização.
- A transcrição é feita localmente com `faster-whisper`; na primeira execução, o modelo pode precisar ser baixado.
- A legenda tradicional usa trechos de fala; a dinâmica apresenta uma palavra por vez.
- Legendas são incorporadas à imagem (não podem ser desativadas no player). O arquivo SRT separado é editável.
- A transcrição pode cometer erros, especialmente com nomes próprios, música e ruído.
- O vídeo sem legendas permanece salvo. A adição de legendas exige uma renderização extra, aumentando o tempo de processamento.
- Para inserir legendas, o FFmpeg precisa ter suporte a **libass**.
- A ativação é feita por checkbox: escrever “adicione legendas” no prompt, isoladamente, não substitui a opção visual nesta versão.
- Não foi validado em Windows nesta sessão; faça um teste curto antes de processar vídeos longos.
