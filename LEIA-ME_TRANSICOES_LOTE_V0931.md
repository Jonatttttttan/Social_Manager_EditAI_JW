# EditAI Videos JW v0.9.3.1 — Transições no lote

Na aba **Editar vários vídeos**, selecione um efeito e duração em **Transições automáticas para todos os vídeos**. O mesmo efeito é aplicado **dentro de cada vídeo**, entre os trechos mantidos pela edição automática. Os vídeos de entrada **não são unidos uns aos outros**.

Opções: Nenhuma, Dissolver, Fade para preto e Deslizar; duração de 0,2 a 2 segundos. O padrão Nenhuma preserva o comportamento anterior.

Se um vídeo possuir apenas um trecho preservado, não há transição. Se a duração exceder o trecho mais curto, aquele vídeo pode falhar e a falha será indicada no relatório do lote, sem interromper os demais. Reduza a duração e tente novamente.

## Testar

Execute o editor com seu ambiente Python 3.12, mantenha o servidor local de licenças ligado e use dois vídeos que gerem múltiplos cortes. Selecione Dissolver com 0,7 s e exporte o lote. Confira os MP4 e `relatorio.json` dentro do ZIP de saída.
