# EditAI Videos JW 0.9.8.3 — Kit para gerar instalador Windows

Este ZIP inclui o codigo completo da v0.9.8.3 (com tolerancia offline de 24h), os binarios FFmpeg/FFprobe e scripts de empacotamento PyInstaller + Inno Setup 6.

**Nao inclui instalador .exe precompilado.** Compilacao Windows precisa ser executada no Windows. O .exe final nao exige Python no computador do testador.

## No seu computador Windows (compilacao)

1. Extraia este ZIP para uma pasta local, de preferencia sem OneDrive ou caminhos longos.
2. Instale Python 3.12 (64 bits) e Inno Setup 6 (https://jrsoftware.org/isdl.php).
3. Execute `build_windows.bat` com internet. O script cria `.venv`, instala dependencias, executa testes e gera `dist\PromptVideoAI\PromptVideoAI.exe`.
4. **Abra manualmente** `dist\PromptVideoAI\PromptVideoAI.exe`, verifique ativacao online, reinicio, 24h offline e exportacao de video. Se falhar, nao distribua.
5. Execute `criar_instalador_windows.bat`.
6. O instalador final estara em `installer_output\EditAI-Videos-JW-0.9.8.3-beta-offline-24h-Setup.exe`.
7. Teste instalar e desinstalar em uma maquina Windows sem Python. Confirme atalhos, FFmpeg, licenciamento e renderizacao.

## Seguranca e limites

- Nao coloque ADMIN_TOKEN, LICENSE_PEPPER, SECRET_KEY, DATABASE_URL ou .env no aplicativo.
- A URL publica do servidor Render ja esta configurada no cliente.
- O instalador nao deve remover `%LOCALAPPDATA%\EditAI Videos JW\license.json` ao desinstalar.
- Nao assinado digitalmente: Windows SmartScreen pode mostrar aviso; para distribuicao comercial, assine o executavel.
- PyInstaller e Inno Setup devem ser executados no Windows. Este kit nao foi compilado nem testado em Windows neste ambiente.
- A tolerancia offline local e um mecanismo de conveniencia, nao uma defesa inviolavel contra adulteracao.
