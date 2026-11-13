# EditAI Videos JW v0.9.8.4 Beta — Social Manager JW (teste local)

## Alterações
- Na aba **Um vídeo**, após a exportação concluída, surge uma seção opcional **Social Manager JW — Instagram Reels**.
- O usuário mantém a prévia e o download do MP4; a publicação é independente.
- Para testar, informe o **ID da sua conta Instagram** e o **token da Meta** já validado com permissões de publicação. Use exclusivamente a sua própria conta de teste.
- Informe a legenda, clique em **1. Enviar vídeo para preparação**, aguarde o processamento da Meta e, após marcar a confirmação explícita, clique em **2. Publicar Reel agora**.
- Se a Meta ainda indicar `IN_PROGRESS`, aguarde e tente novamente **Publicar**. Não repita o upload enquanto o contêiner anterior estiver processando.
- A aba **Lote** continua sem integração de publicação.

## Segurança e limitações
- O token é recebido em um campo de senha e não é gravado pelo módulo em arquivo ou banco. Entretanto, ele passa pela sessão local Gradio: use apenas em máquina confiável e **não habilite compartilhamento público** da interface.
- O token não é incluído no ZIP, nem no instalador. **Não distribua esta modalidade de teste para clientes**: OAuth será necessário para conexões individuais.
- A API da Meta pode exigir conta profissional, permissões e configurações de app específicas.
- A publicação é real e visível na conta. A exclusão é manual no Instagram.
- Esta versão não faz agendamento, OAuth, renovação de tokens, gestão multiusuário ou postagem em lote.
- Não foi validada uma publicação real nesta compilação nem a geração de instalador Windows neste ambiente. A integração anterior foi validada no Colab.

## Arquitetura
- `promptvideo/integrations/instagram.py`: criar contêiner, upload resumable, verificar status e publicar.
- `promptvideo/ui/gradio_app.py`: painel de publicação opcional somente na edição individual.
- `tests/test_instagram_integration.py`: testes de contrato com requisições simuladas.

## Riscos e responsabilidades do produto
- O fluxo de envio e publicação não é transacional; interrupções de rede podem exigir verificação manual do resultado antes de repetir uma ação.
- Tokens de acesso são credenciais sensíveis; não os inclua em logs, capturas de tela ou relatórios de erro.
- Antes de lançar o beta para terceiros, implementar OAuth, armazenamento criptografado, associação por usuário, revogação, revisão de permissões e tratamento de expiração.
- Testar no Windows o empacotamento PyInstaller/Inno Setup, instalação, edição, exportação e publicação antes de distribuição.
