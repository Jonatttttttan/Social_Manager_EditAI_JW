# PromptVideo AI v0.8 — Preparação para instalador Windows

Esta versão mantém o editor v0.7.3 (MP4/MOV, edição individual/em lote, progresso, Smart Duration e legendas) e atualiza o processo de distribuição. **Não contém um executável Windows pronto**: o empacotamento precisa ser executado e validado em Windows.

## 1. Executar o código-fonte
- Windows 10/11 64-bit; Python **3.12**; `ffmpeg.exe` e `ffprobe.exe` em `bin/`.
- Execute `run_windows.bat` e teste a edição antes de empacotar.

## 2. Criar o executável (no Windows)
1. Copie `ffmpeg.exe` e `ffprobe.exe` para `bin/`. Confira origem e licenças.
2. Execute `build_windows.bat` (instala dependências, roda testes e usa PyInstaller `--onedir`).
3. Execute `dist\PromptVideoAI\PromptVideoAI.exe`. Teste MP4, MOV, áudio, legendas e lote.
4. **Não distribua apenas o EXE**; a pasta `dist\PromptVideoAI` contém dependências indispensáveis.

## 3. Criar o instalador (no Windows)
1. Instale **Inno Setup 6**.
2. Após validar o executável, execute `criar_instalador_windows.bat`.
3. O instalador será criado em `installer_output\PromptVideoAI-0.8.0-beta-Setup.exe`.
4. Teste instalação, abertura, edição, fechamento e desinstalação em outro computador sem Python.

## Limitações importantes
- **Não há instalador compilado neste ZIP.** Os scripts não foram executados em Windows neste ambiente.
- O Whisper pode baixar modelos na primeira utilização; um PC totalmente offline precisará de modelos pré-distribuídos/configurados.
- O pacote pode exigir ajustes adicionais no PyInstaller para bibliotecas nativas e recursos do Gradio.
- FFmpeg, codecs, modelos e dependências têm licenças específicas. Verifique a licença da build escolhida e obrigações de redistribuição antes de publicar.
- O instalador não tem assinatura digital; o Windows pode exibir avisos de reputação.
- O modo Qwen é opcional e **não** está incluído como funcionalidade garantida no executável.
- O aplicativo roda localmente e mantém dados em `%USERPROFILE%\PromptVideoAI`. A desinstalação não apaga automaticamente os vídeos do usuário.

## Critérios de aceite da v0.8
- [ ] `build_windows.bat` termina com sucesso no Windows 10/11.
- [ ] `PromptVideoAI.exe` abre sem Python instalado no computador de teste.
- [ ] Exportação MP4 e MOV, áudio e legendas funcionam.
- [ ] A fila de automação e as barras de progresso funcionam.
- [ ] Instalador instala e desinstala corretamente.
- [ ] Licenças, distribuição de FFmpeg e privacidade revisadas.
