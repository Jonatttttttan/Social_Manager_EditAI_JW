# PromptVideo AI v0.8.4 — Estilos de legenda

Esta versão adiciona seis estilos visuais de legenda: Clássica, Shorts, Palavra destacada, Caixa moderna, Minimalista e Neon. Os estilos são combináveis com os modos **Tradicional** (frases) e **Dinâmica** (uma palavra por vez). Inclui tamanho ajustável de 60% a 160%, posição superior/centro/inferior e suporte na edição individual e em lote.

## Como usar

1. Execute `run_windows.bat` para testes com Python e dependências instaladas.
2. Marque **Adicionar legendas**.
3. Escolha o modo de sincronização, o estilo visual, tamanho e posição.
4. Confirme a edição; o estilo é gravado no MP4. O arquivo SRT separado permanece sem formatação, conforme o padrão SRT.
5. Para o instalador, execute `build_windows.bat` e depois `criar_instalador_windows.bat` em Windows com Inno Setup.

## Notas

- A prévia exata do estilo é o vídeo exportado; não há pré-visualização em tempo real nesta versão.
- “Palavra destacada” no modo Dinâmica destaca a palavra ativa exibindo uma palavra por vez, sem animação de palavras adjacentes.
- FFmpeg deve ter suporte a `libass`; mantenha `ffmpeg.exe` e `ffprobe.exe` em `bin`.
- O executável Windows e o instalador devem ser compilados e testados no Windows; testes Python não garantem compatibilidade da distribuição.
