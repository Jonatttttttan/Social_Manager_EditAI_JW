# PromptVideo AI v0.6 — Smart Duration Free

Base: v0.5.1, mantendo edição, áudio e legendas.

## Como testar

1. Extraia este ZIP em uma nova pasta e mantenha a v0.5.1 como backup.
2. Coloque `ffmpeg.exe` e `ffprobe.exe` em `bin/` ou no PATH.
3. Execute `run_windows.bat` (Python 3.12).
4. Envie MP4 e escreva: `Deixe o vídeo com 5 minutos e melhore o áudio`.
5. Analise a estimativa e o JSON de cortes **antes** de aplicar.
6. Compare com o original e teste também legendas tradicionais e dinâmicas.

## Limitações importantes

- A edição Free remove **apenas silêncios**, sem cortar conteúdo falado para atingir a meta.
- Quando não houver pausas suficientes, a duração final será maior que a meta e haverá aviso.
- Se o original for menor que a meta, não há extensão nem desaceleração.
- A duração é aproximada: concatenação e codificação podem variar ligeiramente.
- A transcrição Whisper só roda quando outra operação ou as legendas a solicitar.
- Mantém o perfil de codificação da v0.5.1; preservar resolução não significa vídeo matematicamente sem perdas.
- Não há garantia de funcionamento em qualquer computador; CPU, memória e vídeo influenciam o tempo.

## Próximas etapas

v0.7 fila de automação; futura edição Pro com análise semântica.
