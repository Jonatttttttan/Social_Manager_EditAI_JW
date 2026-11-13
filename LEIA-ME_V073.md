# PromptVideo AI v0.7.3 — MP4 + MOV e progresso por vídeo

Baseada na v0.7.2. Aceita MP4 e MOV na edição individual e na fila (até 20 arquivos), inclusive misturados. Exporta sempre MP4. Mantém barras de progresso individuais e geral, Smart Duration Free, áudio e legendas.

## Instalação Windows
1. Extraia o ZIP em uma nova pasta, sem sobrescrever a versão anterior.
2. Disponibilize `ffmpeg.exe` e `ffprobe.exe` na pasta `bin/` ou no PATH.
3. Execute `run_windows.bat` e siga as instruções existentes de instalação do ambiente, se necessário.
4. Teste um MOV curto, depois um MP4 e por último um lote misto.

## Compatibilidade
MOV é um contêiner: a capacidade de decodificar depende do codec e do build do FFmpeg. Vídeos HEVC, ProRes e vídeos com HDR podem exigir mais recursos ou perder metadados HDR na saída H.264 SDR. A exportação recodifica para H.264/AAC em MP4; não garante preservação bit a bit. Arquivos sem faixa de áudio são aceitos, mas legendas e análise de fala dependem de áudio.

## Validação
Testes automatizados verificam caminhos, formatos e fluxo; faça teste real no Windows com arquivos MOV de origens diferentes.
