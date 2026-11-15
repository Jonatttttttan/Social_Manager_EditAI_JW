
import json
import math
import os
import re
import subprocess
import unicodedata
import shutil

from pathlib import Path
from fractions import Fraction
from promptvideo.config import THREADS_FFMPEG


FORMATOS_ENTRADA = frozenset({'.mp4', '.mov'})


def validar_extensao_video(caminho):
    caminho = Path(caminho)

    if caminho.suffix.lower() not in FORMATOS_ENTRADA:
        raise ValueError(
            'Formato não aceito. Envie um vídeo MP4 ou MOV.'
        )

    if not caminho.is_file():
        raise FileNotFoundError(caminho)

    return caminho


def ffmpeg_bin(name):
    # Permite incluir ffmpeg.exe e ffprobe.exe
    # em bin/ na distribuição.
    import sys

    base = Path(
        getattr(
            sys,
            '_MEIPASS',
            Path(__file__).resolve().parents[2]
        )
    )

    candidate = base / 'bin' / (
        name + ('.exe' if sys.platform == 'win32' else '')
    )

    return (
        str(candidate)
        if candidate.is_file()
        else (shutil.which(name) or name)
    )


def flags_subprocess():
    """
    Impede que subprocessos abram janelas
    de terminal no Windows.
    """
    if os.name == 'nt':
        return subprocess.CREATE_NO_WINDOW

    return 0


def executar(cmd, etapa, log=None):
    """
    Executa comandos externos sem abrir console no Windows.

    Preserva:
    - Captura de stdout e stderr
    - Logs de processamento
    - Tratamento de erros
    - Código de retorno
    """

    flags = flags_subprocess()

    if log:
        with open(log, 'w', encoding='utf-8') as f:
            p = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=f,
                creationflags=flags
            )

        if p.returncode:
            linhas = (
                Path(log)
                .read_text(
                    encoding='utf-8',
                    errors='replace'
                )
                .replace('\r', '\n')
                .splitlines()
            )

            raise RuntimeError(
                f'{etapa}: código {p.returncode}. '
                f'Log: {log}\n'
                + '\n'.join(linhas[-18:])
            )

    else:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=flags
        )

        if p.returncode:
            raise RuntimeError(
                f'{etapa}: código {p.returncode}\n'
                + p.stderr[-2500:]
            )

    return p


def analisar_video(caminho):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError(caminho)

    p = executar(
        [
            ffmpeg_bin('ffprobe'),
            '-v', 'error',
            '-show_entries',
            'format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate',
            '-of', 'json',
            str(caminho)
        ],
        'ffprobe'
    )

    dados = json.loads(p.stdout)
    streams = dados.get('streams', [])

    v = next(
        (
            x for x in streams
            if x.get('codec_type') == 'video'
        ),
        None
    )

    a = next(
        (
            x for x in streams
            if x.get('codec_type') == 'audio'
        ),
        None
    )

    if not v:
        raise ValueError('Vídeo sem fluxo de imagem')

    dur = float(dados['format']['duration'])

    if not math.isfinite(dur) or dur <= 0:
        raise ValueError('Duração inválida')

    try:
        fps = float(
            Fraction(v.get('avg_frame_rate', '30/1'))
        )
    except (ValueError, ZeroDivisionError):
        fps = 30

    if not math.isfinite(fps) or fps <= 0:
        fps = 30

    return {
        'duracao': dur,
        'fps': fps,
        'possui_audio': bool(a),
        'largura': v.get('width'),
        'altura': v.get('height')
    }


def normalizar(s):
    s = unicodedata.normalize(
        'NFD',
        str(s).lower()
    )

    return ''.join(
        c for c in s
        if unicodedata.category(c) != 'Mn'
    )


def juntar_intervalos(intervalos, duracao, folga=0):
    ordenados = sorted(
        (
            max(0., float(a) - folga),
            min(duracao, float(b) + folga)
        )
        for a, b in intervalos
        if float(b) > float(a)
    )

    unidos = []

    for a, b in ordenados:
        if b <= a:
            continue

        if unidos and a <= unidos[-1][1] + 0.015:
            unidos[-1] = (
                unidos[-1][0],
                max(unidos[-1][1], b)
            )
        else:
            unidos.append((a, b))

    return unidos


def trechos_preservados(cortes, duracao):
    unidos = juntar_intervalos(cortes, duracao)

    manter = []
    cursor = 0.

    for a, b in unidos:
        if a > cursor + 0.04:
            manter.append((cursor, a))

        cursor = max(cursor, b)

    if duracao > cursor + 0.04:
        manter.append((cursor, duracao))

    return manter
