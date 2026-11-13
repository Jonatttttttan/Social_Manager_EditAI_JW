
"""Transições de vídeo com FFmpeg xfade e áudio com acrossfade."""

import math
from pathlib import Path

from promptvideo.core.media import executar, ffmpeg_bin
from promptvideo.config import THREADS_FFMPEG, CRF_VIDEO, PRESET_VIDEO


TRANSICOES = {
    "Nenhuma": None,
    "Dissolver": "fade",
    "Fade para preto": "fadeblack",
    "Deslizar": "slideleft",
}


def validar_transicao(nome, duracao):
    """Valida o efeito e a duração da transição."""

    if nome not in TRANSICOES:
        raise ValueError("Transição inválida.")

    try:
        segundos = float(duracao)
    except (ValueError, TypeError):
        raise ValueError("Duração da transição inválida.")

    if not math.isfinite(segundos) or not 0.2 <= segundos <= 2.0:
        raise ValueError(
            "A duração da transição deve estar entre 0,2 e 2 segundos."
        )

    return segundos


def unir_com_transicoes(
    arquivos,
    duracoes,
    saida,
    nome,
    segundos,
    fps,
    possui_audio,
    pasta,
):
    """
    Une os trechos com transições de vídeo e áudio.

    Normaliza FPS, PTS, timebase e formato de vídeo antes
    de aplicar xfade, reduzindo problemas de timestamps.

    Não modifica os arquivos de entrada.
    """

    segundos = validar_transicao(nome, segundos)

    if nome == "Nenhuma" or len(arquivos) < 2:
        raise ValueError(
            "Transições requerem dois ou mais trechos "
            "e um efeito ativo."
        )

    if len(duracoes) != len(arquivos):
        raise ValueError(
            "A quantidade de durações deve corresponder "
            "à quantidade de arquivos."
        )

    try:
        fps = float(fps)
    except (TypeError, ValueError):
        raise ValueError("FPS inválido.")

    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("FPS inválido.")

    # Representação racional compatível com FFmpeg.
    from fractions import Fraction

    fps_fracao = Fraction(fps).limit_denominator(100000)
    fps_ffmpeg = (
        f"{fps_fracao.numerator}/{fps_fracao.denominator}"
    )

    duracoes = [float(d) for d in duracoes]

    if any(not math.isfinite(d) or d <= 0 for d in duracoes):
        raise ValueError("As durações dos trechos devem ser positivas.")

    menor = min(duracoes)

    if segundos >= menor - 0.08:
        raise ValueError(
            f"Transição de {segundos:g}s longa demais "
            f"para o menor trecho ({menor:.2f}s). "
            "Reduza a duração."
        )

    entradas = []

    for arquivo in arquivos:
        entradas.extend(["-i", str(arquivo)])

    filtros = []

    # Normaliza todos os trechos antes das transições.
    #
    # fps: padroniza a taxa de quadros.
    # setpts: reinicia os timestamps.
    # settb: estabelece uma timebase comum.
    # format: padroniza o formato de pixels.
    # setsar: normaliza a proporção dos pixels.

    for i in range(len(arquivos)):
        filtros.append(
            f"[{i}:v:0]"
            f"fps={fps_ffmpeg},"
            f"settb=AVTB,"
            f"setpts=PTS-STARTPTS,"
            f"format=yuv420p,"
            f"setsar=1"
            f"[v{i}]"
        )

        if possui_audio:
            filtros.append(
                f"[{i}:a:0]"
                f"aresample=48000:first_pts=0,"
                f"asetpts=PTS-STARTPTS"
                f"[a{i}]"
            )

    video = "v0"
    audio = "a0"

    acumulado = duracoes[0]

    # Constrói a cadeia de transições.
    for i in range(1, len(arquivos)):
        offset = max(0.0, acumulado - segundos)

        filtros.append(
            f"[{video}][v{i}]"
            f"xfade="
            f"transition={TRANSICOES[nome]}:"
            f"duration={segundos:.6f}:"
            f"offset={offset:.6f}"
            f"[vx{i}]"
        )

        video = f"vx{i}"

        if possui_audio:
            filtros.append(
                f"[{audio}][a{i}]"
                f"acrossfade="
                f"d={segundos:.6f}:"
                f"c1=tri:"
                f"c2=tri"
                f"[ax{i}]"
            )

            audio = f"ax{i}"

        acumulado += duracoes[i] - segundos

    cmd = [
        ffmpeg_bin("ffmpeg"),
        "-y",
        "-hide_banner",
        "-nostdin",
        "-nostats",
        "-filter_complex_threads",
        "1",
        "-threads",
        str(THREADS_FFMPEG),
        *entradas,
        "-filter_complex",
        ";".join(filtros),
        "-map",
        f"[{video}]",
    ]

    if possui_audio:
        cmd.extend(["-map", f"[{audio}]"])

    cmd.extend([
        "-c:v",
        "libx264",
        "-threads",
        str(THREADS_FFMPEG),
        "-preset",
        PRESET_VIDEO,
        "-crf",
        str(CRF_VIDEO),
        "-pix_fmt",
        "yuv420p",
        "-r",
        fps_ffmpeg,
        "-fps_mode:v",
        "cfr",
    ])

    if possui_audio:
        cmd.extend([
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-ac",
            "2",
        ])

    cmd.extend([
        "-movflags",
        "+faststart",
        "-avoid_negative_ts",
        "make_zero",
        str(saida),
    ])

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)

    executar(
        cmd,
        "Transições",
        pasta / "transicoes.log",
    )

    saida = Path(saida)

    if not saida.is_file() or saida.stat().st_size == 0:
        raise RuntimeError(
            "O vídeo com transições não foi gerado."
        )
