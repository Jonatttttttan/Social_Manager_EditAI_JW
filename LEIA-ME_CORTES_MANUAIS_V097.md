# EditAI Videos JW v0.9.7 — Cortes manuais

Na aba **Um vídeo**, abra **✂️ Remover trechos manualmente**. Assista ao vídeo original e informe um intervalo por linha, por exemplo `02:30 - 03:15` ou `00:02:30 - 00:03:15`.

Os intervalos são sempre relativos ao arquivo original. Os cortes manuais são combinados aos cortes automáticos; sobreposições são fundidas. A operação não modifica o original. O modo lote não aplica cortes manuais nesta versão, pois os vídeos podem ter durações diferentes.

## Testes
Execute `python -m unittest discover -s tests -v`. Depois teste um vídeo curto no Windows, incluindo áudio, legendas, filtros e transições. A auditoria completa de segurança permanece pendente.
