"""Efeitos sonoros locais programados no tempo do vídeo final."""
import math
import os
import re
import tempfile
from pathlib import Path
from promptvideo.core.media import analisar_video, executar, ffmpeg_bin
from promptvideo.features.background_music import validar_volume

EFFECT_DIR = Path(__file__).resolve().parents[1] / 'effects'
EFFECTS = tuple(sorted(p.stem for p in EFFECT_DIR.glob('*.wav')))
TIME_RE = re.compile(r'^(\d{2,}):([0-5]\d)(?:\.(\d{1,3}))?$')

def tempo_segundos(value):
    value = str(value).strip()
    m = TIME_RE.fullmatch(value)
    if not m:
        raise ValueError(f'Horário inválido: {value!r}. Use MM:SS ou MM:SS.mmm.')
    return int(m[1])*60+int(m[2])+float('0.'+(m[3] or '0'))

def aplicar_efeitos(video, eventos, callback=None):
    video = Path(video)
    eventos = eventos or []
    if hasattr(eventos, 'values'):
        eventos = eventos.values.tolist()
    duracao = float(analisar_video(video)['duracao'])
    validos = []
    for i, row in enumerate(eventos, 1):
        if not row or not any(str(v).strip() for v in row):
            continue
        if len(row) < 3:
            raise ValueError(f'Efeito {i}: informe efeito, horário e volume.')
        nome, momento, volume = (str(row[0]).strip(), row[1], row[2])
        if not nome and not str(momento).strip():
            continue
        if nome not in EFFECTS:
            raise ValueError(f'Efeito {i}: escolha um efeito da biblioteca.')
        inicio = tempo_segundos(momento)
        if not 0 <= inicio < duracao:
            raise ValueError(f'Efeito {i}: o início deve estar dentro do vídeo final ({duracao:.1f}s).')
        vol = validar_volume(volume)
        if vol:
            validos.append((nome, inicio, vol))
    if not validos:
        return str(video)
    info = analisar_video(video)
    cmd = [ffmpeg_bin('ffmpeg'), '-y', '-hide_banner', '-nostdin', '-nostats', '-i', str(video)]
    for nome, _, _ in validos:
        cmd += ['-i', str(EFFECT_DIR / (nome+'.wav'))]
    graph=[]
    if info['possui_audio']:
        graph.append('[0:a:0]aresample=48000,aformat=channel_layouts=stereo[base]')
    else:
        graph.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={duracao:.6f}[base]')
    labels=['[base]']
    for idx,(_,inicio,vol) in enumerate(validos,1):
        delay=round(inicio*1000)
        graph.append(f'[{idx}:a:0]aresample=48000,aformat=channel_layouts=stereo,volume={vol/100:.4f},adelay={delay}|{delay}[fx{idx}]')
        labels.append(f'[fx{idx}]')
    graph.append(''.join(labels)+f'amix=inputs={len(labels)}:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[aout]')
    fd,saida=tempfile.mkstemp(suffix='.mp4',prefix='editai_fx_',dir=str(video.parent))
    os.close(fd)
    try:
        if callback: callback('Adicionando efeitos sonoros')
        cmd += ['-filter_complex',';'.join(graph),'-map','0:v:0','-map','[aout]','-c:v','copy','-c:a','aac','-b:a','192k','-t',f'{duracao:.6f}','-movflags','+faststart',saida]
        executar(cmd,'Efeitos sonoros')
        if not Path(saida).is_file() or not Path(saida).stat().st_size:
            raise RuntimeError('Não foi possível gerar o áudio com efeitos.')
        os.replace(saida,video)
    finally:
        if os.path.exists(saida):os.unlink(saida)
    return str(video)
