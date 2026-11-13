# PromptVideo AI v0.4 — Linguagem Natural Leve

Esta versão parte da v0.3 e preserva o aprimoramento automático de áudio.

## O que mudou
- Mais formas de pedir remoção de pausas e silêncios.
- Interpretação de duração em segundos e pedidos combinados.
- Comandos para reduzir ruído, melhorar voz/volume e remover frases entre aspas.
- Resumo do plano interpretado antes de aplicar a edição.
- Interpretador leve e offline, sem API paga e sem necessidade de GPU.
- Qwen continua opcional via `PROMPTVIDEO_QWEN=1` e `requirements-qwen.txt`; não é instalado por padrão.

## Instalação no Windows
1. Mantenha a v0.3 como backup e extraia este ZIP em uma pasta nova.
2. Copie `ffmpeg.exe` e `ffprobe.exe` da pasta `bin` da v0.3 para a pasta `bin` da v0.4, se necessário.
3. Execute `run_windows.bat`. É necessário Python 3.12 e internet para instalar dependências na primeira execução.
4. Acesse `http://127.0.0.1:7860` e teste com um MP4 curto.

## Exemplos de instruções
- `Tira as pausas grandes e limpa o chiado.`
- `Elimine os silêncios maiores que 2 segundos.`
- `Deixa minha voz mais clara.`
- `Corta quando eu disser "vou recomeçar".`
- `Não remova os silêncios, apenas melhore o áudio.`

## Limitações
- O interpretador leve usa padrões e sinônimos, não entende toda frase possível.
- Pedidos como legendas animadas ou resumir semanticamente o vídeo não são suportados.
- A melhoria de áudio já é automática desde a v0.3; um pedido isolado de áudio não ativa uma segunda passagem adicional.
- O resumo de interpretação ajuda na revisão, mas não garante que cortes por transcrição estejam perfeitos.
- Requisitos de RAM e desempenho em PCs de 4 GB ainda precisam ser testados.
- O código foi testado com testes unitários locais; o fluxo Gradio/FFmpeg deve ser validado no Windows.

## Testes
`python -m unittest discover -s tests -v`
