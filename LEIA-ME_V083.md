# PromptVideo AI v0.8.3 — Instalador Windows

Esta versão **preserva o código de edição da v0.8.2** e atualiza a distribuição Windows.

## Preparação

1. Extraia o ZIP numa pasta nova. Não execute scripts dentro do ZIP.
2. Tenha Windows 10/11 64 bits, Python 3.12 e Inno Setup 6 **somente na máquina de compilação**.
3. Coloque `ffmpeg.exe` e `ffprobe.exe` em `bin/` (os binários não são redistribuídos neste ZIP).
4. Execute `build_windows.bat` e teste `dist\PromptVideoAI\PromptVideoAI.exe` editando e exportando um vídeo.
5. Execute `criar_instalador_windows.bat`.
6. O instalador ficará em `installer_output\PromptVideoAI-0.8.3-beta-Setup.exe`.

## Teste obrigatório antes de enviar a clientes

- Instale com o instalador em Windows sem Python instalado, preferencialmente em uma VM limpa.
- Confirme atalhos do menu Iniciar e opcional da área de trabalho.
- Confirme abertura da interface e acesso pelo navegador local.
- Importe MP4 e MOV; faça corte, tratamento de áudio, legendas e exportação MP4.
- Verifique que `ffmpeg` e `ffprobe` funcionam dentro do pacote.
- Teste modelos Whisper em primeiro uso com rede disponível e depois sem rede; downloads iniciais podem ser necessários.
- Desinstale via Configurações do Windows e verifique os atalhos.
- Faça uma instalação por cima da v0.8.3 para validar atualização.

## Limitações

Este ZIP **não contém um instalador pré-compilado**, pois a compilação PyInstaller e Inno Setup precisa ser executada no Windows. A validação aqui é estrutural e não substitui o teste real. A assinatura digital do executável, a distribuição de modelos offline e uma política de atualizações automáticas não fazem parte desta versão. Evite distribuir sem avaliar licenças de dependências e binários FFmpeg.

O instalador é por usuário, sem exigir privilégios de administrador, e preserva o mesmo AppId da v0.8.2 para upgrades.
