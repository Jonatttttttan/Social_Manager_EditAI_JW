# EditAI Videos JW v0.9.4 — Música de fundo

A edição individual e a edição em lote agora permitem selecionar uma das três trilhas originais sintetizadas e incluídas, ou importar MP3, WAV, M4A, AAC, FLAC e OGG. Há pré-escuta, volume de 0–100%, opção de preservar o áudio original e fades de entrada e saída. O áudio é adicionado após a edição e legendagem, usando FFmpeg e mantendo o vídeo sem recodificação adicional.

## Instalação

Copie `ffmpeg.exe` e `ffprobe.exe` para `bin/` e execute `main.py` no ambiente Python existente. Para PyInstaller, use o `PromptVideoAI.spec` atualizado, que inclui as trilhas.

## Atenção

As trilhas incluídas são composições instrumentais sintéticas originais, curtas e repetidas automaticamente para acompanhar o vídeo. O arquivo próprio deve ser usado apenas se o usuário possuir direitos de uso. Volume de 100% significa ganho nominal da trilha, não volume final normalizado; misturas altas podem causar clipping. A edição em lote usa a mesma trilha em cada vídeo, exportados separadamente. O aplicativo continua exigindo o servidor de licenças configurado.
