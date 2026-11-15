"""Zoom temporal suave no vídeo final, com ancoragem esquerda/centro/direita."""
import math
import os
import re
import tempfile
from pathlib import Path

from promptvideo.core.media import analisar_video, executar, ffmpeg_bin

_HORARIO = re.compile(r'^(\d{1,3}):([0-5]\d)(?:\.(\d{1,3}))?$')
_POSICOES = {'Esquerda': '0', 'Centro': '(iw-iw/zoom)/2', 'Direita': '(iw-iw/zoom)'}
_INTENSIDADES = {'1.2x': 1.2, '1.5x': 1.5, '2.0x': 2.0}


def _segundos(valor):
    valor = str(valor).strip()
    m = _HORARIO.fullmatch(valor)
    if not m:
        raise ValueError(f'Horário de zoom inválido: {valor!r}. Use MM:SS ou MM:SS.mmm.')
    return int(m[1]) * 60 + int(m[2]) + int((m[3] or '0').ljust(3, '0')) / 1000


def validar_zooms(linhas, duracao):
    if hasattr(linhas, 'values'):
        linhas = linhas.values.tolist()
    resultado = []
    for indice, linha in enumerate(linhas or [], 1):
        if not linha or not any(str(v).strip() for v in linha):
            continue
        if len(linha) != 4:
            raise ValueError(f'Zoom {indice}: preencha posição, início, fim e intensidade.')
        pos, inicio, fim, intensidade = (str(v).strip() for v in linha)
        if pos not in _POSICOES or intensidade not in _INTENSIDADES:
            raise ValueError(f'Zoom {indice}: posição ou intensidade inválida.')
        a, b = _segundos(inicio), _segundos(fim)
        if not 0 <= a < b <= duracao + 0.02:
            raise ValueError(f'Zoom {indice}: o intervalo deve estar dentro do vídeo final ({duracao:.2f}s), com início menor que fim.')
        resultado.append((a, b, pos, _INTENSIDADES[intensidade]))
    resultado.sort()
    for anterior, atual in zip(resultado, resultado[1:]):
        if atual[0] < anterior[1] - 0.001:
            raise ValueError('Os intervalos de zoom não podem se sobrepor.')
    return resultado


def _expressao_zoom(intervalos, fps):
    """Uma expressão por frame: rampa suave de entrada e saída, com patamar."""
    expr = '1'
    for a, b, _pos, escala in reversed(intervalos):
        inicio, fim = a * fps, b * fps
        rampa = min((fim - inicio) / 3, fps * 0.5)
        rampa = max(rampa, 0.001)
        # Rampa suave (smoothstep) evita saltos no início e no fim.
        u = f'min(1,max(0,(on-{inicio:.5f})/{rampa:.5f}))'
        v = f'min(1,max(0,({fim:.5f}-on)/{rampa:.5f}))'
        entrada = f'({u}*{u}*(3-2*{u}))'
        saida = f'({v}*{v}*(3-2*{v}))'
        valor = f'(1+{escala-1:.4f}*min({entrada},{saida}))'
        expr = f'if(between(on,{inicio:.5f},{fim:.5f}),{valor},{expr})'
    return expr


def _expressao_posicao(intervalos, fps):
    # Ancoragem interpolada: fora do intervalo, o zoom é 1 e a posição é irrelevante.
    expr = _POSICOES['Centro']
    for a, b, pos, _ in reversed(intervalos):
        expr = f'if(between(on,{a*fps:.5f},{b*fps:.5f}),{_POSICOES[pos]},{expr})'
    return expr


def aplicar_zoom(video, linhas, callback=None):
    video = Path(video)
    info = analisar_video(video)
    intervalos = validar_zooms(linhas, info['duracao'])
    if not intervalos:
        return str(video)
    fps = min(60.0, max(1.0, float(info['fps'])))
    w, h = int(info['largura']), int(info['altura'])
    if w % 2: w -= 1
    if h % 2: h -= 1
    if w < 2 or h < 2:
        raise ValueError('Resolução do vídeo inválida para zoom.')
    # zoompan trabalha em frames individuais (d=1), sem alterar o áudio.
    zoom = _expressao_zoom(intervalos, fps)
    x = _expressao_posicao(intervalos, fps)
    y = '(ih-ih/zoom)/2'
    graph = f"zoompan=z='{zoom}':x='{x}':y='{y}':d=1:s={w}x{h}:fps={fps:.6f},format=yuv420p"
    fd, destino = tempfile.mkstemp(prefix='editai_zoom_', suffix='.mp4', dir=str(video.parent))
    os.close(fd)
    try:
        if callback: callback('Aplicando zoom suave aos intervalos selecionados')
        cmd = [ffmpeg_bin('ffmpeg'), '-y', '-hide_banner', '-nostdin', '-nostats', '-i', str(video), '-map', '0:v:0']
        if info['possui_audio']:
            cmd += ['-map', '0:a:0', '-c:a', 'copy']
        else:
            cmd += ['-an']
        cmd += ['-vf', graph, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', destino]
        executar(cmd, 'Zoom programável')
        if not Path(destino).is_file() or Path(destino).stat().st_size == 0:
            raise RuntimeError('Falha ao exportar vídeo com zoom.')
        os.replace(destino, video)
    finally:
        if os.path.exists(destino): os.unlink(destino)
    return str(video)
