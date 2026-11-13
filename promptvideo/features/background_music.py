"""Música de fundo aplicada ao MP4 final, preservando a edição e o áudio original."""
import math
import os
import tempfile
from pathlib import Path
from promptvideo.core.media import analisar_video, executar, ffmpeg_bin

MUSIC_DIR = Path(__file__).resolve().parents[1] / 'music'
TRACKS = ('Sem música', 'Ambient Suave', 'Piano Calmo', 'Energia Leve', 'Arquivo próprio')
EXTENSIONS = frozenset(('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg'))

def escolher_musica(nome='Sem música', arquivo=None):
    if nome not in TRACKS:
        raise ValueError('Trilha não reconhecida.')
    if nome == 'Sem música':
        return None
    if nome == 'Arquivo próprio':
        if not arquivo:
            raise ValueError('Selecione um arquivo de áudio para a trilha própria.')
        p = Path(arquivo)
        if not p.is_file() or p.suffix.lower() not in EXTENSIONS:
            raise ValueError('Arquivo de música inválido. Use MP3, WAV, M4A, AAC, FLAC ou OGG.')
        return p
    p = MUSIC_DIR / (nome + '.wav')
    if not p.is_file():
        raise FileNotFoundError(f'Trilha integrada ausente: {p.name}')
    return p

def validar_volume(volume):
    v = float(volume)
    if not math.isfinite(v) or not 0 <= v <= 100:
        raise ValueError('O volume deve estar entre 0 e 100%.')
    return v

def adicionar_musica(video, trilha='Sem música', arquivo=None, volume=20, manter_original=True, fade=True, callback=None):
    musica = escolher_musica(trilha, arquivo)
    vol = validar_volume(volume)
    video = Path(video)
    if musica is None or vol == 0:
        return str(video)
    info = analisar_video(video)
    duracao = info['duracao']
    # Loop no input e duração limitada pelo vídeo. Fade-out sempre dentro do tempo final.
    fade_dur = min(1.5, duracao / 3)
    filtros = [f'[1:a:0]volume={vol/100:.4f},aresample=48000,aformat=channel_layouts=stereo']
    if fade:
        filtros.append(f'afade=t=in:st=0:d={fade_dur:.3f},afade=t=out:st={max(0,duracao-fade_dur):.3f}:d={fade_dur:.3f}')
    filtros.append(f'atrim=duration={duracao:.6f},asetpts=PTS-STARTPTS[music]')
    graph = ','.join(filtros)
    misturar = bool(manter_original and info['possui_audio'])
    if misturar:
        graph += ';[0:a:0]aresample=48000,aformat=channel_layouts=stereo[original];[original][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]'
    else:
        graph += ';[music]anull[aout]'
    fd, saida = tempfile.mkstemp(suffix='.mp4', prefix='editai_musica_', dir=str(video.parent))
    os.close(fd)
    try:
        if callback: callback('Adicionando música de fundo')
        cmd = [ffmpeg_bin('ffmpeg'), '-y', '-hide_banner', '-nostdin', '-nostats', '-i', str(video), '-stream_loop', '-1', '-i', str(musica), '-filter_complex', graph, '-map', '0:v:0', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', f'{duracao:.6f}', '-movflags', '+faststart', saida]
        executar(cmd, 'Música de fundo')
        if not Path(saida).is_file() or Path(saida).stat().st_size == 0:
            raise RuntimeError('Falha ao produzir áudio com música.')
        os.replace(saida, video)
    finally:
        if os.path.exists(saida): os.unlink(saida)
    return str(video)
