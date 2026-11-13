# PromptVideo AI v0.7 — Fila de automação

## Novidades
- Seleção de até 20 vídeos MP4 para processamento sequencial.
- Uma instrução em linguagem natural aplicada a todos os arquivos.
- Legendas tradicionais ou dinâmicas opcionais.
- ZIP de resultados com `relatorio.json` indicando sucessos e falhas.
- Falha em um vídeo não impede a execução dos próximos.

## Instalação Windows
1. Extraia o ZIP em uma nova pasta (mantenha a v0.6 como backup).
2. Copie `ffmpeg.exe` e `ffprobe.exe` para `bin/` ou configure-os no PATH.
3. Execute `run_windows.bat` e abra a interface local.
4. Na seção **Fila de automação**, selecione vídeos, digite uma instrução e clique em **Processar fila**.
5. Baixe o ZIP e confira o relatório e os vídeos.

## Limitações e segurança
- Não executa edições semânticas com LLM; só aplica cortes calculados pelo motor Free.
- Não permite revisar cortes individualmente antes da execução em lote. Use a edição individual quando precisar revisar.
- Pode consumir tempo e disco; teste primeiro com 2 vídeos curtos.
- Os arquivos são processados localmente; não habilite `share=True` no Gradio.
- Não é instalador: ainda requer Python/venv e FFmpeg, como nas versões anteriores.
