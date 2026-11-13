
"""Diagnóstico sem acesso à rede nem leitura de vídeos pessoais."""

import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys

from pathlib import Path

from promptvideo.core.media import ffmpeg_bin
from promptvideo.config import BASE, ENTRADAS, SAIDAS


def diagnosticar():
    resultado = {
        'python': sys.version.split()[0],
        'sistema': platform.platform(),
        'executavel': sys.executable,
        'diretorio_dados': str(BASE),
        'dependencias': {
            nome: importlib.util.find_spec(nome) is not None
            for nome in (
                'gradio',
                'faster_whisper',
                'ctranslate2'
            )
        },
        'ferramentas': {},
    }

    # Impede a abertura de janelas de terminal no Windows.
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    for nome in ('ffmpeg', 'ffprobe'):
        binario = ffmpeg_bin(nome)

        try:
            proc = subprocess.run(
                [binario, '-version'],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=flags
            )

            resultado['ferramentas'][nome] = {
                'encontrado': proc.returncode == 0,
                'caminho': binario,
                'versao': (
                    proc.stdout.splitlines()[0]
                    if proc.stdout else ''
                )
            }

        except (OSError, subprocess.TimeoutExpired) as exc:
            resultado['ferramentas'][nome] = {
                'encontrado': False,
                'caminho': binario,
                'erro': str(exc)
            }

    try:
        uso = shutil.disk_usage(BASE)

        resultado['espaco_livre_gb'] = round(
            uso.free / (1024**3),
            2
        )

        resultado['pastas_gravaveis'] = all(
            os.access(p, os.W_OK)
            for p in (BASE, ENTRADAS, SAIDAS)
        )

    except OSError as exc:
        resultado['erro_armazenamento'] = str(exc)

    return resultado


if __name__ == '__main__':
    print(
        json.dumps(
            diagnosticar(),
            ensure_ascii=False,
            indent=2
        )
    )
