"""Filtros visuais com presets restritos e validação de parâmetros."""
import math
import os
import tempfile
from pathlib import Path
from promptvideo.core.media import analisar_video, executar, ffmpeg_bin

FILTROS = ('Original', 'Cinematográfico quente', 'Cinematográfico frio', 'Preto e branco', 'Vintage', 'Vibrante', 'Suave')
# Valores fixos: nenhum texto do usuário é interpolado como expressão FFmpeg.
_PRESETS = {
    'Original': (0.0, 1.0, 1.0, 0.0, 0.0),
    'Cinematográfico quente': (0.015, 1.10, 1.12, 0.11, -0.05),
    'Cinematográfico frio': (-0.012, 1.12, 0.94, -0.08, 0.12),
    'Preto e branco': (0.0, 1.12, 0.0, 0.0, 0.0),
    'Vintage': (0.02, 0.90, 0.72, 0.08, -0.04),
    'Vibrante': (0.0, 1.09, 1.40, 0.02, 0.0),
    'Suave': (0.02, 0.88, 0.90, 0.035, 0.015),
}

def validar_filtros(filtro='Original', intensidade=60, brilho=0, contraste=0):
    if filtro not in _PRESETS:
        raise ValueError('Filtro visual não reconhecido.')
    valores = []
    for nome, valor, minimo, maximo in (('intensidade', intensidade, 0, 100), ('brilho', brilho, -100, 100), ('contraste', contraste, -100, 100)):
        try:
            numero = float(valor)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'{nome} inválido.') from exc
        if not math.isfinite(numero) or not minimo <= numero <= maximo:
            raise ValueError(f'{nome} fora do intervalo permitido.')
        valores.append(numero)
    return tuple(valores)

def montar_filtro(filtro='Original', intensidade=60, brilho=0, contraste=0):
    intensidade, brilho, contraste = validar_filtros(filtro, intensidade, brilho, contraste)
    t = intensidade / 100
    b, c, s, r, blue = _PRESETS[filtro]
    b = b * t + brilho / 100 * 0.25
    c = 1 + (c - 1) * t + contraste / 100 * 0.5
    s = 1 + (s - 1) * t
    r *= t
    blue *= t
    if filtro == 'Original' and brilho == 0 and contraste == 0 or (t == 0 and brilho == 0 and contraste == 0):
        return None
    return f'eq=brightness={b:.5f}:contrast={c:.5f}:saturation={s:.5f},colorbalance=rs={r:.5f}:bs={blue:.5f}'

def aplicar_filtro_video(video, filtro='Original', intensidade=60, brilho=0, contraste=0, callback=None):
    graph = montar_filtro(filtro, intensidade, brilho, contraste)
    video = Path(video)
    if graph is None:
        return str(video)
    info = analisar_video(video)
    fd, temp = tempfile.mkstemp(prefix='editai_filtro_', suffix='.mp4', dir=str(video.parent))
    os.close(fd)
    try:
        if callback: callback('Aplicando filtro visual')
        cmd = [ffmpeg_bin('ffmpeg'), '-y', '-hide_banner', '-nostdin', '-nostats', '-i', str(video), '-map', '0:v:0']
        if info['possui_audio']:
            cmd += ['-map', '0:a:0', '-c:a', 'copy']
        else:
            cmd += ['-an']
        cmd += ['-vf', graph, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', temp]
        executar(cmd, 'Filtro visual')
        if not Path(temp).is_file() or Path(temp).stat().st_size == 0:
            raise RuntimeError('Falha ao produzir vídeo com filtro visual.')
        os.replace(temp, video)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return str(video)
