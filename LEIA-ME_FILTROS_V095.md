# EditAI Videos JW v0.9.5 Beta — Filtros visuais

Inclui seis presets: Cinematográfico quente, Cinematográfico frio, Preto e branco, Vintage, Vibrante e Suave, além do modo Original. Controles de intensidade (0–100%), brilho (-100 a 100) e contraste (-100 a 100) na edição individual e em lote. Os filtros são aplicados ao MP4 final, preservando a faixa de áudio. A aplicação exige nova codificação do vídeo e pode demorar em arquivos longos.

## Segurança
Os filtros são escolhidos por uma lista fixa; valores numéricos são limitados e não são interpolados como comandos do sistema. O FFmpeg é chamado sem shell. Esta revisão é pontual e não equivale a auditoria integral de segurança do projeto ou das dependências. Teste em vídeos de exemplo antes de distribuir.

## Executar
Copie ffmpeg.exe e ffprobe.exe para bin/, use seu ambiente Python 3.12 existente e execute `python main.py`. Não sobrescreva a versão 0.9.4 até validar esta versão.
