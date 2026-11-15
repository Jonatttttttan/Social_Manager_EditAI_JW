"""Melhoria automática de áudio no arquivo final (FFmpeg, loudnorm em 2 passagens)."""
import json
import math
import re
import shutil
from pathlib import Path

from promptvideo.core.media import analisar_video, executar, ffmpeg_bin

# Configuração inicial para vídeos com fala. Não é restauração de áudio.
ALVO_LUFS = -16
PICO_MAX_DBTP = -1.5
LRA_ALVO = 11


def _filtro_base():
    # highpass suave e compressão moderada antes da medição.
    return 'highpass=f=80,acompressor=threshold=0.125:ratio=2:attack=20:release=200'


def _medir_loudnorm(caminho):
    filtro = f'{_filtro_base()},loudnorm=I={ALVO_LUFS}:TP={PICO_MAX_DBTP}:LRA={LRA_ALVO}:print_format=json'
    cmd = [ffmpeg_bin('ffmpeg'), '-hide_banner', '-nostdin', '-i', str(caminho),
           '-map', '0:a:0', '-vn', '-af', filtro, '-f', 'null', '-']
    p = executar(cmd, 'Medição de áudio')
    # FFmpeg escreve o relatório JSON em stderr.
    blocos = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', p.stderr, flags=re.S)
    if not blocos:
        raise RuntimeError('FFmpeg não retornou a medição de loudnorm.')
    dados = json.loads(blocos[-1])
    campos = ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset')
    for campo in campos:
        valor = str(dados[campo])
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            raise ValueError(f'Medição de áudio inválida: {campo}={valor}')
        if not math.isfinite(numero):
            # -inf ocorre em silêncio ou material curto demais para o loudnorm.
            # Não é seguro passar essas medições para a segunda passagem.
            return None
    return dados


def melhorar_audio(entrada, saida):
    """Aplica tratamento no MP4 inteiro, sem recodificar o vídeo.

    Retorna o caminho de saída. Se não houver áudio, apenas copia o vídeo.
    """
    entrada, saida = Path(entrada), Path(saida)
    if entrada.resolve() == saida.resolve():
        raise ValueError('A saída deve ser diferente da entrada.')
    saida.parent.mkdir(parents=True, exist_ok=True)
    if not analisar_video(entrada)['possui_audio']:
        shutil.copy2(entrada, saida)
        return saida
    med = _medir_loudnorm(entrada)
    if med is None:
        # Preserva o arquivo original/intermediário sem inventar ganho para silêncio.
        print('[Áudio] Medição loudnorm indisponível (-inf/NaN). Preservando áudio sem normalização.', flush=True)
        shutil.copy2(entrada, saida)
        return saida
    filtro = (f'{_filtro_base()},loudnorm=I={ALVO_LUFS}:TP={PICO_MAX_DBTP}:LRA={LRA_ALVO}'
              f':measured_I={med["input_i"]}:measured_TP={med["input_tp"]}'
              f':measured_LRA={med["input_lra"]}:measured_thresh={med["input_thresh"]}'
              f':offset={med["target_offset"]}:linear=true:print_format=summary')
    cmd = [ffmpeg_bin('ffmpeg'), '-y', '-hide_banner', '-nostdin', '-i', str(entrada),
           '-map', '0:v:0', '-map', '0:a:0', '-c:v', 'copy', '-af', filtro,
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
           '-movflags', '+faststart', str(saida)]
    executar(cmd, 'Melhoria automática de áudio')
    if not saida.is_file() or saida.stat().st_size == 0:
        raise RuntimeError('Arquivo de áudio aprimorado vazio.')
    return saida
