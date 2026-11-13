"""Legendas opcionais: SRT editável e ASS renderizado no MP4.
Versão de diagnóstico: registra FFmpeg/ffprobe e testa normalização temporal.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import logging
import json
import shlex
from datetime import datetime

from promptvideo.core.media import analisar_video, ffmpeg_bin
from promptvideo.features.audio import transcrever


def _srt_time(t):
    ms = max(0, round(float(t) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def _ass_time(t):
    cs = max(0, round(float(t) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'


def _clean(text):
    return re.sub(r'\s+', ' ', str(text)).strip()


def _ass_escape(text):
    return (_clean(text).replace('\\', '＼').replace('{', '（')
            .replace('}', '）'))


def _chunks(segments, max_chars=74):
    result = []
    for s in segments:
        words = s.get('palavras') or []
        if words:
            group = []
            for w in words:
                word = _clean(w.get('texto', ''))
                if not word:
                    continue
                if group and len(' '.join(x[2] for x in group)) + len(word) + 1 > max_chars:
                    result.append((group[0][0], group[-1][1], _clean(' '.join(x[2] for x in group))))
                    group = []
                group.append((float(w['inicio']), float(w['fim']), word))
            if group:
                result.append((group[0][0], group[-1][1], _clean(' '.join(x[2] for x in group))))
        elif _clean(s.get('texto', '')):
            result.append((float(s['inicio']), float(s['fim']), _clean(s['texto'])))
    return [(a, max(b, a + .05), t) for a, b, t in result if t]


def _srt(cues):
    return '\n\n'.join(f'{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{t}'
                       for i, (a, b, t) in enumerate(cues, 1)) + '\n'


ESTILOS_VISUAIS = ('Clássica', 'Shorts', 'Palavra destacada', 'Caixa moderna', 'Minimalista', 'Neon')
PRESETS = {
    'Clássica': dict(cor='&H00FFFFFF', destaque='&H0000FFFF', borda='&H00000000', fundo='&H80000000', escala=1.00, outline=2, shadow=1, border=1, bold=-1),
    'Shorts': dict(cor='&H0000DFFF', destaque='&H0000FFFF', borda='&H00000000', fundo='&H80000000', escala=1.22, outline=4, shadow=1, border=1, bold=-1),
    'Palavra destacada': dict(cor='&H00FFFFFF', destaque='&H0000FFFF', borda='&H00000000', fundo='&H80000000', escala=1.12, outline=3, shadow=1, border=1, bold=-1),
    'Caixa moderna': dict(cor='&H00FFFFFF', destaque='&H0000FFFF', borda='&H00000000', fundo='&H70000000', escala=1.00, outline=0, shadow=0, border=3, bold=-1),
    'Minimalista': dict(cor='&H00FFFFFF', destaque='&H0000FFFF', borda='&H00000000', fundo='&H80000000', escala=.90, outline=0, shadow=0, border=1, bold=0),
    'Neon': dict(cor='&H00F5F355', destaque='&H0000FFFF', borda='&H00332200', fundo='&H80000000', escala=1.18, outline=3, shadow=1, border=1, bold=-1),
}
POSICOES = {'Inferior': 2, 'Centro': 5, 'Superior': 8}


def validar_aparencia(visual='Clássica', tamanho=100, posicao='Inferior'):
    if visual not in ESTILOS_VISUAIS:
        raise ValueError('Estilo visual inválido.')
    if posicao not in POSICOES:
        raise ValueError('Posição de legenda inválida.')
    try:
        tamanho = int(tamanho)
    except (ValueError, TypeError):
        raise ValueError('Tamanho de legenda inválido.')
    if not 60 <= tamanho <= 160:
        raise ValueError('Tamanho da legenda deve ficar entre 60% e 160%.')
    return visual, tamanho, posicao


def _ass_header(w, h, visual='Clássica', tamanho=100, posicao='Inferior'):
    visual, tamanho, posicao = validar_aparencia(visual, tamanho, posicao)
    preset = PRESETS[visual]
    fontsize = max(18, min(120, round(h * .047 * preset['escala'] * tamanho / 100)))
    margin = max(18, round(h * .07))
    align = POSICOES[posicao]
    style = (
        f"Arial,{fontsize},{preset['cor']},{preset['destaque']},"
        f"{preset['borda']},{preset['fundo']},{preset['bold']},0,0,0,100,100,0,0,"
        f"{preset['border']},{preset['outline']},{preset['shadow']},{align},25,25,{margin},1"
    )
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Tradicional,{style}
Style: Dinamica,{style}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass(segments, style, w, h, visual='Clássica', tamanho=100, posicao='Inferior'):
    lines = [_ass_header(w, h, visual, tamanho, posicao)]
    if style == 'Tradicional':
        for a, b, t in _chunks(segments):
            lines.append(f'Dialogue: 0,{_ass_time(a)},{_ass_time(b)},Tradicional,,0,0,0,,{_ass_escape(t)}\n')
    elif style == 'Dinâmica':
        for s in segments:
            words = s.get('palavras') or []
            if words:
                for word in words:
                    t = _ass_escape(word.get('texto', ''))
                    if t:
                        a = float(word['inicio'])
                        b = max(float(word['fim']), a + .06)
                        lines.append(f'Dialogue: 0,{_ass_time(a)},{_ass_time(b)},Dinamica,,0,0,0,,{t}\n')
            elif _clean(s.get('texto', '')):
                a = float(s['inicio'])
                b = max(float(s['fim']), a + .06)
                lines.append(f'Dialogue: 0,{_ass_time(a)},{_ass_time(b)},Dinamica,,0,0,0,,{_ass_escape(s["texto"])}\n')
    else:
        raise ValueError('Modo de legenda inválido')
    return ''.join(lines)


def _flags():
    return subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def _log_dir():
    root = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.local' / 'share'))
    folder = root / 'EditAI Videos JW' / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _probe(caminho, log):
    cmd = [ffmpeg_bin('ffprobe'), '-v', 'error', '-show_entries',
           'format=duration,size:stream=index,codec_type,codec_name,time_base,start_time,duration,avg_frame_rate',
           '-of', 'json', str(caminho)]
    p = subprocess.run(cmd, capture_output=True, text=True, errors='replace', creationflags=_flags())
    log.write(f'FFPROBE {caminho}\nreturncode={p.returncode}\n{p.stdout}\n{p.stderr}\n\n')
    if p.returncode != 0:
        raise RuntimeError(f'Falha ao validar MP4 com ffprobe: {p.stderr[-1000:]}')
    data = json.loads(p.stdout)
    streams = data.get('streams', [])
    if not any(s.get('codec_type') == 'video' for s in streams):
        raise RuntimeError('MP4 gerado não possui fluxo de vídeo.')
    return data


def legendar_video(video_editado, estilo='Tradicional', callback=None,
                   visual='Clássica', tamanho=100, posicao='Inferior'):
    """Retorna (mp4_legendado, srt); nunca sobrescreve vídeo sem legendas."""
    validar_aparencia(visual, tamanho, posicao)
    video = Path(video_editado).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    info = analisar_video(video)
    if not info['possui_audio']:
        raise ValueError('Este vídeo não possui áudio para transcrever.')
    if callback:
        callback(0.05, 'Transcrevendo falas para as legendas (tempo variável)')
    segmentos = transcrever(video)
    if callback:
        callback(0.55, 'Preparando legendas')
    if not segmentos:
        raise ValueError('Nenhuma fala identificada para gerar legendas.')
    cues = _chunks(segmentos)
    if not cues:
        raise ValueError('Não foi possível identificar falas com tempos válidos.')
    destino = video.with_name(video.stem + '_legendado.mp4')
    srt = video.with_name(video.stem + '.srt')
    log_path = _log_dir() / ('legendas_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.log')

    with open(log_path, 'w', encoding='utf-8', errors='replace') as log:
        log.write('EditAI - Diagnóstico de legendas\n')
        log.write(f'Entrada: {video}\nSaída: {destino}\n')
        log.write(f'Estilo: {estilo} / {visual} / {tamanho} / {posicao}\n')
        with tempfile.TemporaryDirectory(prefix='promptvideo_legendas_') as temp:
            tmp = Path(temp)
            (tmp / 'legendas.ass').write_text(
                _ass(segmentos, estilo, int(info['largura'] or 1920),
                     int(info['altura'] or 1080), visual, tamanho, posicao),
                encoding='utf-8-sig')
            saida_tmp = tmp / 'video_legendado.mp4'
            _probe(video, log)
            cmd = [
                ffmpeg_bin('ffmpeg'), '-y', '-hide_banner', '-nostdin', '-nostats',
                '-i', str(video),
                '-vf', 'ass=legendas.ass,setpts=PTS-STARTPTS',
                '-map', '0:v:0', '-map', '0:a:0',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k',
                '-af', 'aresample=async=1:first_pts=0',
                '-avoid_negative_ts', 'make_zero', '-movflags', '+faststart',
                str(saida_tmp)
            ]
            log.write('FFMPEG COMMAND:\n' + subprocess.list2cmdline(cmd) + '\n\n')
            log.flush()
            if callback:
                callback(0.65, 'Inserindo legendas no vídeo')
            with open(log_path, 'a', encoding='utf-8', errors='replace') as ff_log:
                p = subprocess.run(cmd, cwd=tmp, stdout=subprocess.DEVNULL,
                                   stderr=ff_log, creationflags=_flags())
            log.seek(0, os.SEEK_END)
            if p.returncode != 0:
                raise RuntimeError(
                    f'Erro ao inserir legendas. FFmpeg retornou {p.returncode}. '
                    f'Log completo: {log_path}'
                )
            if not saida_tmp.is_file() or saida_tmp.stat().st_size == 0:
                raise RuntimeError(f'MP4 legendado vazio. Log: {log_path}')
            _probe(saida_tmp, log)
            os.replace(saida_tmp, destino)
        srt.write_text(_srt(cues), encoding='utf-8-sig')
        log.write(f'\nSUCESSO: {destino}\nSRT: {srt}\n')
    if callback:
        callback(1.0, 'Legendas concluídas')
    return str(destino), str(srt)
