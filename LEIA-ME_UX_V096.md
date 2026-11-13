# EditAI Videos JW v0.9.6 Beta — Redesign da interface

Esta versão parte do código-fonte da v0.9.5 e altera principalmente `promptvideo/ui/gradio_app.py`.

## Mudanças
- Cabeçalho mais compacto, com identidade visual consistente.
- Fluxo visível: importar, personalizar, exportar.
- Títulos de etapas mais claros e botões principais destacados.
- Controles opcionais de transição, música e filtros agrupados em painéis recolhidos e colunas responsivas.
- Melhor adaptação a telas menores, estados de foco visíveis e respeito à preferência de movimento reduzido.
- Compatibilidade de aplicação do CSS com Gradio 5 e 6.

## O que não mudou
O processamento de vídeo, filtros, música, transições, licenciamento e rotas do servidor não foram alterados. As opções de edição individual e em lote continuam disponíveis.

## Execução no Windows
1. Extraia o ZIP em pasta separada da versão anterior.
2. Coloque `ffmpeg.exe` e `ffprobe.exe` em `bin/`, se necessário.
3. Abra o PowerShell na pasta que contém `main.py`.
4. Execute com o Python do seu ambiente virtual já configurado, por exemplo:

```powershell
& "C:\EditAI\Editor\EditAI_Videos_JW_v0.9.2_Licenciamento_Beta\.venv\Scripts\python.exe" main.py
```

5. Mantenha o servidor de licenças local funcionando para os testes.

## Validação
- 50 testes automatizados passaram no ambiente de desenvolvimento.
- A interface foi inicializada com Gradio 6.5.1 sem erros.
- Ainda é necessário verificar o layout visual e a exportação no seu Windows antes de substituir a versão anterior.

## Segurança
Esta atualização é predominantemente visual. Ela **não** substitui a auditoria de segurança completa combinada para o beta. Não inclua `.env`, tokens ou senhas ao publicar o projeto.
