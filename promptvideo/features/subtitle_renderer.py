"""Renderizacao de legendas previamente transcritas."""

from promptvideo.core.performance import medir_etapa
import os
import math
import shutil
import subprocess
import tempfile

from pathlib import Path
from datetime import datetime
from uuid import uuid4

from promptvideo.core.media import analisar_video, ffmpeg_bin

from promptvideo.features.subtitles import (
    _ass,
    _srt,
    _chunks,
    _flags,
    _probe,
    _log_dir,
    validar_aparencia,
)

from promptvideo.features.subtitle_storage import (
    carregar_transcricao,
)


def renderizar_legendas_salvas(
    video_base,
    arquivo_json,
    callback=None
):
    """Renderiza MP4 e SRT sem executar novamente o Whisper."""

    video = Path(video_base).resolve()

    if not video.is_file():
        raise FileNotFoundError(video)

    dados = carregar_transcricao(arquivo_json)
    segmentos = dados["segmentos"]
    config = dados["configuracoes"]

    from promptvideo.features.subtitle_storage import (
        normalizar_config_transicoes,
    )

    from promptvideo.features.edge_transitions import (
        planejar_transicoes,
        construir_filtros_transicoes,
    )

    transicoes = normalizar_config_transicoes(
        config.get("transicoes")
    )

    estilo = config["estilo"]

    if estilo not in ("Tradicional", "Din\u00e2mica"):
        raise ValueError("Modo de legenda invalido.")

    visual, tamanho, posicao = validar_aparencia(
        config["visual"],
        config["tamanho"],
        config["posicao"]
    )

    info = analisar_video(video)
    duracao = float(info["duracao"])

    if not math.isfinite(duracao) or duracao <= 0:
        raise ValueError("Duracao do video invalida.")

    for segmento in segmentos:
        registros = [segmento] + (
            segmento.get("palavras") or []
        )

        for registro in registros:
            inicio = float(registro["inicio"])
            fim = float(registro["fim"])

            if (
                not math.isfinite(inicio)
                or not math.isfinite(fim)
                or inicio < 0
                or fim <= inicio
                or fim > duracao + 0.05
            ):
                raise ValueError(
                    "Intervalo de legenda fora do video."
                )

    plano_transicoes = planejar_transicoes(
        duracao,
        **transicoes
    )

    filtros_transicoes = construir_filtros_transicoes(
        plano_transicoes
    )

    filtros_video = "ass=legendas.ass,setpts=PTS-STARTPTS"

    if filtros_transicoes:
        filtros_video += "," + filtros_transicoes

    cues = _chunks(segmentos)

    if not cues:
        raise ValueError("Nenhuma legenda valida.")

    if callback:
        callback(0.05, "Preparando legendas salvas")

    identificador = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_" + uuid4().hex[:12]
    )

    pasta_final = video.parent / (
        video.stem + "_revisao_" + identificador
    )

    log_path = _log_dir() / (
        "revisao_legendas_" + identificador + ".log"
    )

    with tempfile.TemporaryDirectory(
        prefix=".revisao_legendas_",
        dir=video.parent
    ) as temporario:

        tmp = Path(temporario)
        ass_path = tmp / "legendas.ass"
        mp4_tmp = tmp / "video_corrigido.mp4"
        srt_tmp = tmp / "legendas_corrigidas.srt"

        ass_path.write_text(
            _ass(
                segmentos,
                estilo,
                int(info["largura"] or 1920),
                int(info["altura"] or 1080),
                visual,
                tamanho,
                posicao
            ),
            encoding="utf-8-sig"
        )

        srt_tmp.write_text(
            _srt(cues),
            encoding="utf-8-sig"
        )

        cmd = [
            ffmpeg_bin("ffmpeg"),
            "-y",
            "-hide_banner",
            "-nostdin",
            "-nostats",
            "-i", str(video),
            "-vf", filtros_video,
            "-map", "0:v:0",
        ]

        tem_audio = bool(info.get("possui_audio"))

        if tem_audio:
            cmd += ["-map", "0:a:0"]

        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
        ]

        if tem_audio:
            cmd += [
                "-c:a", "aac",
                "-b:a", "192k",
                "-af", "aresample=async=1:first_pts=0",
            ]

        cmd += [
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            str(mp4_tmp)
        ]

        if callback:
            mensagem = (
                "Renderizando legendas e transicoes"
                if filtros_transicoes
                else "Renderizando legendas corrigidas"
            )

            callback(0.25, mensagem)

        with log_path.open(
            "w", encoding="utf-8", errors="replace"
        ) as log:

            log.write("Entrada: " + str(video) + "\n")
            log.write(subprocess.list2cmdline(cmd) + "\n")

            _probe(video, log)
            log.flush()

            with medir_etapa('ffmpeg.legendas'):
                processo = subprocess.run(
                    cmd,
                    cwd=tmp,
                    stdout=subprocess.DEVNULL,
                    stderr=log,
                    creationflags=_flags()
                )

            if processo.returncode != 0:
                raise RuntimeError(
                    "Falha ao renderizar legendas. Log: "
                    + str(log_path)
                )

            if not mp4_tmp.is_file():
                raise RuntimeError("Video corrigido nao gerado.")

            if mp4_tmp.stat().st_size == 0:
                raise RuntimeError("Video corrigido vazio.")

            _probe(mp4_tmp, log)

        if callback:
            callback(0.95, "Salvando nova exportacao")

        pasta_final.mkdir(exist_ok=False)

        mp4_final = pasta_final / mp4_tmp.name
        srt_final = pasta_final / srt_tmp.name

        try:
            os.replace(mp4_tmp, mp4_final)
            os.replace(srt_tmp, srt_final)

        except Exception:
            shutil.rmtree(pasta_final)
            raise

    if callback:
        callback(1.0, "Legendas corrigidas com sucesso")

    from gradio.processing_utils import save_file_to_cache
    from gradio.utils import get_upload_folder

    cache_dir = get_upload_folder()
    mp4_cache = save_file_to_cache(str(mp4_final), cache_dir)
    srt_cache = save_file_to_cache(str(srt_final), cache_dir)

    return str(mp4_cache), str(srt_cache)
