"""Monitoramento opcional de desempenho do motor."""

import json
import os
import threading
import time

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


_LOCK = threading.Lock()


def monitoramento_ativo():
    return os.getenv("EDITAI_PERFORMANCE", "0") == "1"


def registrar_desempenho(registro):
    try:
        destino = Path(
            os.getenv(
                "EDITAI_PERFORMANCE_LOG",
                "logs/performance.jsonl"
            )
        )

        linha = json.dumps(
            registro,
            ensure_ascii=False,
            allow_nan=False
        )

        with _LOCK:
            destino.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with destino.open("a", encoding="utf-8") as arquivo:
                arquivo.write(linha + "\n")

    except Exception:
        # Monitoring must not interrupt video editing.
        pass


@contextmanager
def medir_etapa(nome):
    if not monitoramento_ativo():
        yield
        return

    inicio = time.perf_counter()
    horario = datetime.now(timezone.utc).isoformat()
    sucesso = False

    try:
        yield
        sucesso = True

    finally:
        duracao = time.perf_counter() - inicio

        registrar_desempenho({
            "etapa": str(nome),
            "horario_utc": horario,
            "duracao_segundos": round(duracao, 6),
            "sucesso": sucesso,
            "pid": os.getpid(),
            "thread": threading.get_ident()
        })
