# EditAI Videos JW v0.9.2 — Licenciamento (beta local)

## O que mudou
- Tela de ativação antes de abrir a interface Gradio.
- Identificador aleatório persistente por instalação, salvo em `%LOCALAPPDATA%\EditAI Videos JW\license.json`.
- Ativação em `POST /api/licenses/activate` e validação em `POST /api/licenses/validate`.
- Verificação online ao iniciar e antes de analisar, editar e processar lotes.
- Sem chave administrativa nem LICENSE_PEPPER no aplicativo.

## Como testar no Windows
1. Inicie o EditAI License Server JW v0.2, com banco PostgreSQL funcionando.
2. No painel `/panel/`, crie uma **nova licença ativa** de teste; não use as revogadas.
3. Nesta pasta, crie o ambiente Python 3.12 e instale `requirements.txt` conforme README existente, ou reaproveite o ambiente de desenvolvimento.
4. Execute `INICIAR_EDITOR_LICENCIADO_WINDOWS.bat`.
5. Informe a chave no formulário de ativação. O navegador abrirá o editor após validação.
6. Revogue a licença no painel e tente uma nova análise/edição; a operação deverá ser bloqueada.

O endereço padrão é `http://127.0.0.1:5000`. Para trocar, configure a variável de ambiente `EDITAI_LICENSE_SERVER` **antes de executar o editor**. O `.bat` de testes fixa o endereço local.

## Limitações desta versão
- Exige conexão com o servidor em cada operação protegida; **não há modo offline**.
- A validação é feita no cliente Python: não é proteção anticópia ou antiviolação forte.
- A chave de ativação não é salva, mas o token é salvo em JSON local sem criptografia. Para produção, migrar para armazenamento protegido pelo Windows (DPAPI).
- Não foi compilado nem testado em Windows neste ambiente; execute os testes e gere o instalador com os scripts existentes.
- Antes de distribuir externamente, hospede o servidor atrás de HTTPS com controles de segurança adequados.
- O código presume que o endpoint de ativação responde com `activation_token` e que o de validação responde com `valid: true`. Se a implementação real diferir, adapte o cliente.
