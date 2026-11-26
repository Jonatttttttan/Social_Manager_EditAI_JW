import json
import math
import subprocess

from fractions import Fraction
from pathlib import Path

from promptvideo.core.media import ffmpeg_bin


def verificar_copia_direta(video):
    """Avalia conservadoramente a compatibilidade da midia."""

    try:
        video = Path(video)

        if not video.is_file():
            return False, "Arquivo inexistente"

        if video.suffix.lower() != ".mp4":
            return False, "Extensao diferente de MP4"

        processo = subprocess.run(
            [
                ffmpeg_bin("ffprobe"),
                "-v", "error",
                "-show_streams",
                "-show_format",
                "-of", "json",
                str(video)
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            creationflags=getattr(
                subprocess, "CREATE_NO_WINDOW", 0
            )
        )

        if processo.returncode != 0:
            return False, "Falha na analise da midia"

        dados = json.loads(processo.stdout)
        formato = dados["format"]
        streams = dados["streams"]

        videos = [
            s for s in streams
            if s.get("codec_type") == "video"
        ]

        audios = [
            s for s in streams
            if s.get("codec_type") == "audio"
        ]

        if len(videos) != 1 or len(audios) > 1:
            return False, "Quantidade de fluxos incompat?vel"

        if len(streams) != len(videos) + len(audios):
            return False, "Fluxos adicionais"

        if "mp4" not in formato.get("format_name", "").split(","):
            return False, "Container incompat?vel"

        marca = formato.get("tags", {}).get("major_brand", "")

        if marca not in ("isom", "iso2", "mp41", "mp42", "avc1"):
            return False, "Marca do container incompat?vel"

        v = videos[0]

        requisitos = [
            ("codec_name", "h264"),
            ("codec_tag_string", "avc1"),
            ("pix_fmt", "yuv420p"),
            ("sample_aspect_ratio", "1:1"),
            ("field_order", "progressive")
        ]

        for chave, esperado in requisitos:
            if v.get(chave) != esperado:
                return False, "Video incompat?vel: " + chave

        if v.get("disposition", {}).get("attached_pic"):
            return False, "Imagem anexada"

        if v.get("side_data_list"):
            return False, "Metadados laterais presentes"

        if "rotate" in v.get("tags", {}):
            return False, "Metadados de rotacao"

        largura = int(v["width"])
        altura = int(v["height"])

        if min(largura, altura) < 2:
            return False, "Resolucao invalida"

        if largura % 2 or altura % 2:
            return False, "Resolucao impar"

        fps = Fraction(v["avg_frame_rate"])
        fps_nominal = Fraction(v["r_frame_rate"])

        if fps != fps_nominal or not 1 <= fps <= 60:
            return False, "FPS incompat?vel"

        duracao = float(formato["duration"])
        duracao_video = float(v["duration"])

        if not all(
            math.isfinite(x) and x > 0
            for x in (duracao, duracao_video)
        ):
            return False, "Duracao invalida"

        if abs(duracao - duracao_video) > 0.05:
            return False, "Duracoes divergentes"

        if abs(float(formato["start_time"])) > 0.001:
            return False, "Inicio do container incompat?vel"

        if abs(float(v["start_time"])) > 0.001:
            return False, "Inicio do video incompat?vel"

        quadros = int(v["nb_frames"])

        if abs(quadros - duracao_video * float(fps)) > 1:
            return False, "Contagem de quadros incompat?vel"

        if audios:
            a = audios[0]

            if a.get("codec_name") != "aac":
                return False, "Codec de audio incompat?vel"

            if a.get("profile") != "LC":
                return False, "Perfil AAC incompat?vel"

            if int(a["sample_rate"]) != 48000:
                return False, "Taxa de audio incompat?vel"

            if int(a["channels"]) != 2:
                return False, "Audio requer normalizacao para estereo"

            if a.get("channel_layout") != "stereo":
                return False, "Layout de audio incompat?vel"

            if abs(float(a["start_time"])) > 0.001:
                return False, "Inicio do audio incompat?vel"

            duracao_audio = float(a["duration"])

            if not math.isfinite(duracao_audio):
                return False, "Duracao de audio invalida"

            if abs(duracao_audio - duracao_video) > 0.05:
                return False, "Duracoes de audio e video divergentes"

        return True, "Compatibilidade preliminar aprovada"

    except Exception as erro:
        return False, "Analise inconclusiva: " + str(erro)


def tentar_copia_direta(origem, destino):
    """Copia midia compativel sem recodificar."""

    import os
    import shutil
    import tempfile

    temporario = None

    try:
        origem = Path(origem).resolve()
        destino = Path(destino).resolve()

        if origem == destino:
            return False, "Origem e destino iguais"

        if destino.exists() and origem.samefile(destino):
            return False, "Origem e destino equivalentes"

        if destino.suffix.lower() != ".mp4":
            return False, "Destino incompat?vel"

        aprovado, motivo = verificar_copia_direta(origem)

        if not aprovado:
            return False, motivo

        estado = origem.stat()

        destino.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            prefix=".fast_path_",
            suffix=".mp4",
            dir=destino.parent,
            delete=False
        ) as f:
            temporario = Path(f.name)

        shutil.copy2(origem, temporario)

        atual = origem.stat()

        if (
            atual.st_size != estado.st_size
            or atual.st_mtime_ns != estado.st_mtime_ns
        ):
            return False, "Origem alterada durante a copia"

        if temporario.stat().st_size != estado.st_size:
            return False, "Tamanho da copia divergente"

        os.replace(temporario, destino)

        return True, "Copia direta concluida"

    except Exception as erro:
        return False, "Falha na copia: " + str(erro)

    finally:
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass
