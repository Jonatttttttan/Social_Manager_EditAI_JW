# PromptVideo AI v0.3 — Melhoria automática de áudio

Esta versão adiciona normalização de volume **automática** em toda exportação MP4 com áudio. A edição original continua funcionando normalmente.

## Instalação no projeto que já funciona

1. Feche o terminal do PromptVideo AI.
2. Faça uma cópia de segurança da pasta atual.
3. Copie **`promptvideo/features/audio_enhancer.py`** para a pasta correspondente do projeto existente.
4. Substitua **`promptvideo/core/render.py`** pelo arquivo desta versão.
5. Execute `run_windows.bat` normalmente e teste um vídeo curto.

Alternativamente, extraia este ZIP em uma **nova pasta** e execute o projeto por lá, mantendo os arquivos `ffmpeg.exe` e `ffprobe.exe` na pasta `bin/` (ou disponíveis no PATH). Verifique se o `run_windows.bat` está usando Python 3.12 em sua máquina.

## Como funciona

- Preserva a remoção de silêncios e os outros cortes existentes.
- Após concatenar os trechos, aplica filtro passa-altas de 80 Hz, compressão leve e normalização de sonoridade `loudnorm` em duas passagens.
- Meta inicial: -16 LUFS, pico verdadeiro máximo -1,5 dBTP, LRA 11.
- O vídeo não é recodificado nessa etapa (`-c:v copy`); o áudio final é codificado em AAC 192 kb/s.
- Vídeos sem áudio não recebem tratamento.
- Se houver erro no tratamento, a exportação falha sem substituir o arquivo final por um arquivo incompleto.

**Observação:** o resultado pode soar diferente dependendo do material original; não é um sistema de restauração de voz nem garantia de aumento de volume em todos os casos. Compare a exportação com o original, especialmente em vídeos com música.
