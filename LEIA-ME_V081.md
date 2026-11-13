# PromptVideo AI v0.8.1 — correção de empacotamento

## Problema corrigido
O executável criado pelo PyInstaller encerrava durante a importação do Gradio porque faltava `_internal\safehttpx\version.txt`.

## Alteração
O script `build_windows.bat` agora inclui `--collect-data safehttpx` no comando PyInstaller, para empacotar os dados da biblioteca. O arquivo `PromptVideoAI.spec` é gerado automaticamente pelo comando e **não precisa ser editado**.

## Como reconstruir no Windows
1. Extraia esta versão em uma pasta nova.
2. Copie `ffmpeg.exe` e `ffprobe.exe` da instalação anterior para `bin`.
3. Execute `build_windows.bat` e aguarde a conclusão.
4. Abra um CMD dentro de `dist\PromptVideoAI` e execute `PromptVideoAI.exe`.
5. Se iniciar, teste uma edição curta e depois execute `criar_instalador_windows.bat` com o Inno Setup instalado.

**Nota:** este pacote contém código-fonte e scripts; não contém o `.exe` Windows já compilado. A compilação e a validação precisam ocorrer no Windows. A correção resolve especificamente o recurso ausente do safehttpx; outras dependências podem exigir ajustes adicionais.
