# EditAI Videos JW v0.9.8.3 — Beta offline 24 horas

Versão completa do código do editor v0.9.8.2 com atualização do cliente de licenciamento para tolerância offline de 24 horas.

## Para usar no Windows
1. Extraia a pasta `EditAI_Videos_JW_v0.9.8.3` para um local de sua preferência.
2. Instale Python 3.12 se ainda não estiver disponível.
3. Com internet, dê dois cliques em `INICIAR_EDITOR_LICENCIADO_WINDOWS.bat`. Na primeira execução, as dependências Python serão instaladas na pasta `.venv` (pode demorar).
4. Ative uma licença válida do servidor Render, se necessário.
5. Depois de uma validação online bem-sucedida, teste fechar o editor, desligar a internet e abrir novamente. A tolerância dura até 24 horas e nunca ultrapassa a validade da licença.

## Notas
- O pacote inclui o código-fonte e os executáveis FFmpeg/FFprobe fornecidos na versão anterior. Não é um instalador `.exe` pronto.
- A pasta `.venv` original foi intencionalmente omitida: ambientes virtuais não são portáteis entre computadores e podem conter caminhos absolutos.
- O servidor de licenças padrão é `https://editai-license-server-jw.onrender.com`; não é necessário configurar o endereço manualmente.
- O arquivo de licença fica em `%LOCALAPPDATA%\EditAI Videos JW\license.json`, compartilhado com versões anteriores. Não exclua esse arquivo.
- Em caso de recusa explícita do servidor (licença revogada/expirada), o editor bloqueia; somente falhas de conexão permitem a tolerância offline.
- Uma cópia de `license.json` pode ser adulterada por usuários avançados. Para proteção comercial mais forte, usar autorização offline assinada pelo servidor.
- Requer testes manuais no Windows antes de distribuição pública.
