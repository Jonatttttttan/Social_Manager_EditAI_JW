# PromptVideo AI v0.5.1 — Correção de áudio e legendas

## Correções

- Fixa `av==16.1.0`, compatível com o argumento `metadata_errors` utilizado pelo `faster-whisper` instalado no teste.
- Se o FFmpeg retornar `input_i=-inf` ou outra medição não finita, preserva o MP4 intermediário sem aplicar normalização. Isso evita a interrupção, mas **não recupera áudio ausente ou silencioso**.
- Mantém a interface, as legendas tradicionais/dinâmicas e a edição da v0.5.

## Instalação no Windows

1. Preserve a v0.5 como backup e extraia esta v0.5.1 em outra pasta.
2. Copie `ffmpeg.exe` e `ffprobe.exe` para `bin/` da nova pasta.
3. Execute `run_windows.bat` (Python 3.12). Ele instalará as dependências no ambiente da nova pasta.
4. Teste com um vídeo curto com fala e a opção de legenda tradicional. Depois teste a dinâmica.

## Atenção: cortes excessivos

O log anterior indicou apenas dois trechos preservados de 0,15 s e 0,20 s. Se o JSON de cortes mostrar que quase todo o vídeo será removido, **não aplique a edição**: revise os intervalos primeiro. O tratamento de `-inf` evita uma exceção, mas não corrige propostas de cortes equivocadas.

Esta correção foi validada com testes locais; ainda não foi executada no seu Windows.
