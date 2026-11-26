
from promptvideo.core.performance import medir_etapa
import re
import os
import subprocess
import threading

from pathlib import Path

from promptvideo.config import THREADS_FFMPEG, MODELO_WHISPER
from promptvideo.core.media import ffmpeg_bin


def detectar_silencios(caminho, duracao, limite_db=-35., minimo=1., margem=0.15):
    cmd = [
        ffmpeg_bin('ffmpeg'),
        '-hide_banner',
        '-nostdin',
        '-nostats',
        '-threads',
        str(THREADS_FFMPEG),
        '-i',
        str(caminho),
        '-vn',
        '-af',
        f'silencedetect=noise={limite_db}dB:d={minimo}',
        '-f',
        'null',
        '-'
    ]

    # Impede que o FFmpeg abra janelas de terminal no Windows.
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    with medir_etapa('ffmpeg.audio'):
        p = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=flags
        )

    if p.returncode:
        raise RuntimeError(
            'Falha na detecção de silêncio: ' + p.stderr[-1500:]
        )

    eventos = re.findall(
        r'silence_(start|end):\s*([0-9.]+)',
        p.stderr
    )

    silencios = []
    inicio = None

    for tipo, valor in eventos:
        t = float(valor)

        if tipo == 'start':
            inicio = t

        elif inicio is not None:
            if t > inicio:
                silencios.append((inicio, t))

            inicio = None

    if inicio is not None:
        silencios.append((inicio, duracao))

    # Mantém margem nas extremidades do silêncio
    # para não cortar sílabas.
    return [
        (a + margem, b - margem)
        for a, b in silencios
        if b - a > 2 * margem + 0.04
    ]


_whisper = None
_whisper_nome = None
_lock_whisper = threading.Lock()



def _liberar_whisper_se_necessario():
    """Executar somente com o lock do Whisper adquirido."""

    global _whisper, _whisper_nome

    if _whisper is None:
        return False

    from promptvideo.core.memory_manager import (
        deve_liberar_whisper
    )

    liberar, motivo = deve_liberar_whisper()

    if not liberar:
        return False

    import gc
    import logging

    with medir_etapa("whisper.liberar_cache"):
        _whisper = None
        _whisper_nome = None
        gc.collect()

    logging.getLogger(__name__).info(
        "Cache Whisper liberado: %s",
        motivo
    )

    return True


def transcrever(caminho, modelo=None):
    global _whisper, _whisper_nome

    from promptvideo.core.whisper_manager import carregar_modelo_whisper

    with _lock_whisper:
        try:
            if _whisper is None or _whisper_nome != (modelo or MODELO_WHISPER):
                nome = modelo or MODELO_WHISPER

                # CPU int8: menor consumo de memória;
                # não exige GPU.
                _whisper = carregar_modelo_whisper(nome)

                _whisper_nome = nome

            segmentos, info = _whisper.transcribe(
                str(caminho),
                language='pt',
                beam_size=3,
                vad_filter=True,
                word_timestamps=True
            )

            saida = []

            for s in segmentos:
                palavras = [
                    {
                        'inicio': round(w.start, 3),
                        'fim': round(w.end, 3),
                        'texto': w.word
                    }
                    for w in (s.words or [])
                ]

                saida.append({
                    'inicio': round(s.start, 3),
                    'fim': round(s.end, 3),
                    'texto': s.text.strip(),
                    'palavras': palavras
                })

            return saida

        finally:
            _liberar_whisper_se_necessario()


def filtro_ruido(nivel):
    # afftdn é uma redução espectral;
    # não elimina perfeitamente vozes,
    # música ou sons variáveis.
    return {
        'leve': 'afftdn=nr=8:nf=-35',
        'medio': 'afftdn=nr=12:nf=-35',
        'forte': 'afftdn=nr=18:nf=-35'
    }.get(nivel)
