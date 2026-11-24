
import json
import math
import os
import shutil
import subprocess
import tempfile

from fractions import Fraction
from pathlib import Path

from promptvideo.config import (
    THREADS_FFMPEG,
    CRF_VIDEO,
    PRESET_VIDEO,
    MAX_TRECHOS,
)

from promptvideo.core.media import (
    analisar_video,
    trechos_preservados,
    executar,
    ffmpeg_bin,
)

from promptvideo.core.transitions import (
    validar_transicao,
    unir_com_transicoes,
)

from promptvideo.features.audio import filtro_ruido
from promptvideo.features.audio_enhancer import melhorar_audio


# ============================================================
# UTILITÁRIOS
# ============================================================

def _fps_ffmpeg(valor):
    """
    Converte FPS para uma fração compatível com FFmpeg.
    """
    fps = float(valor)

    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("FPS inválido.")

    fps = max(1.0, min(120.0, fps))

    taxas = (
        Fraction(24000, 1001),
        Fraction(24, 1),
        Fraction(25, 1),
        Fraction(30000, 1001),
        Fraction(30, 1),
        Fraction(50, 1),
        Fraction(60000, 1001),
        Fraction(60, 1),
        Fraction(120, 1),
    )

    for taxa in taxas:
        if abs(float(taxa) - fps) < 0.02:
            return f"{taxa.numerator}/{taxa.denominator}"

    fracao = Fraction(fps).limit_denominator(10000)

    return f"{fracao.numerator}/{fracao.denominator}"


def _executar_ffprobe(caminho):
    """
    Consulta metadados do arquivo usando ffprobe.
    """
    cmd = [
        ffmpeg_bin("ffprobe"),
        "-v",
        "error",
        "-show_entries",
        (
            "format=duration:"
            "stream=index,codec_type,"
            "start_time,duration,"
            "avg_frame_rate,r_frame_rate"
        ),
        "-of",
        "json",
        str(caminho),
    ]

    kwargs = {
        "capture_output": True,
        "text": True,
        "errors": "replace",
    }

    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    resultado = subprocess.run(cmd, **kwargs)

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha no ffprobe para {caminho}:\n"
            f"{resultado.stderr[-3000:]}"
        )

    try:
        return json.loads(resultado.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Resposta JSON inválida do ffprobe: {caminho}"
        ) from exc


def _numero_positivo(valor):
    """
    Converte um valor em número positivo finito.
    """
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numero) or numero <= 0:
        return None

    return numero


def _inicio_fluxo(stream):
    """
    Obtém o início do fluxo.
    """
    try:
        inicio = float(stream.get("start_time", 0))
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(inicio):
        return 0.0

    return inicio


def _fim_fluxo(stream):
    """
    Calcula o instante final de um fluxo.
    """
    duracao = _numero_positivo(stream.get("duration"))

    if duracao is None:
        return None

    return _inicio_fluxo(stream) + duracao


def _duracao_real_video(caminho):
    """
    Obtém o instante final do fluxo de vídeo.

    Prioriza stream.duration em vez de format.duration,
    pois a duração do contêiner pode ser determinada
    pelo áudio, mesmo quando o vídeo termina antes.
    """
    dados = _executar_ffprobe(caminho)

    videos = [
        stream
        for stream in dados.get("streams", [])
        if stream.get("codec_type") == "video"
    ]

    if not videos:
        raise RuntimeError(
            f"Arquivo original sem fluxo de vídeo: {caminho}"
        )

    video = videos[0]
    fim_video = _fim_fluxo(video)

    if fim_video is None:
        # Caso stream.duration não esteja disponível,
        # utiliza a duração do contêiner como fallback.
        # Esse valor é menos preciso e será registrado.
        duracao_formato = _numero_positivo(
            dados.get("format", {}).get("duration")
        )

        if duracao_formato is None:
            raise RuntimeError(
                "Não foi possível determinar a duração "
                f"do fluxo de vídeo: {caminho}"
            )

        fim_video = duracao_formato

        print(
            "[AVISO] stream.duration indisponível. "
            "Usando format.duration como fallback.",
            flush=True,
        )

    audios = [
        stream
        for stream in dados.get("streams", [])
        if stream.get("codec_type") == "audio"
    ]

    print(
        "[MÍDIA] "
        f"Fim do fluxo de vídeo: {fim_video:.6f}s",
        flush=True,
    )

    if audios:
        fim_audio = _fim_fluxo(audios[0])

        if fim_audio is not None:
            print(
                "[MÍDIA] "
                f"Fim do fluxo de áudio: {fim_audio:.6f}s",
                flush=True,
            )

            print(
                "[MÍDIA] "
                f"Diferença original: "
                f"{abs(fim_video - fim_audio):.6f}s",
                flush=True,
            )

    return fim_video


def _validar_duracoes(
    caminho,
    possui_audio,
    tolerancia=1.0,
):
    """
    Verifica a presença dos fluxos e detecta
    diferenças anormais entre áudio e vídeo.

    Não substitui uma inspeção completa de DTS/PTS.
    """
    dados = _executar_ffprobe(caminho)

    streams = dados.get("streams", [])

    videos = [
        stream
        for stream in streams
        if stream.get("codec_type") == "video"
    ]

    audios = [
        stream
        for stream in streams
        if stream.get("codec_type") == "audio"
    ]

    if not videos:
        raise RuntimeError(
            f"Arquivo sem fluxo de vídeo: {caminho}"
        )

    if possui_audio and not audios:
        raise RuntimeError(
            f"Arquivo sem fluxo de áudio: {caminho}"
        )

    fim_video = _fim_fluxo(videos[0])

    if fim_video is None or fim_video <= 0:
        raise RuntimeError(
            f"Duração de vídeo inválida: {caminho}"
        )

    if possui_audio:
        fim_audio = _fim_fluxo(audios[0])

        if fim_audio is None or fim_audio <= 0:
            raise RuntimeError(
                f"Duração de áudio inválida: {caminho}"
            )

        diferenca = abs(fim_video - fim_audio)

        print(
            "[VALIDAÇÃO] "
            f"{Path(caminho).name} | "
            f"Vídeo: {fim_video:.3f}s | "
            f"Áudio: {fim_audio:.3f}s | "
            f"Diferença: {diferenca:.3f}s",
            flush=True,
        )

        if diferenca > tolerancia:
            raise RuntimeError(
                "Durações inconsistentes no arquivo "
                f"{Path(caminho).name}: "
                f"vídeo={fim_video:.3f}s, "
                f"áudio={fim_audio:.3f}s, "
                f"diferença={diferenca:.3f}s."
            )

    return fim_video


# ============================================================
# NORMALIZAÇÃO DOS INTERVALOS
# ============================================================

def _normalizar_intervalos(manter, duracao_video, fps):
    """
    Limita os trechos ao final real do vídeo.

    Descarta somente resíduos finais menores
    que um quadro.

    Não descarta automaticamente intervalos
    curtos localizados no meio do vídeo.
    """
    taxa = float(Fraction(fps))
    duracao_quadro = 1.0 / taxa

    resultado = []

    for indice, (inicio, fim) in enumerate(manter, 1):
        inicio = float(inicio)
        fim = float(fim)

        inicio_ajustado = max(0.0, inicio)
        fim_ajustado = min(fim, duracao_video)

        if inicio_ajustado >= duracao_video:
            print(
                "[INTERVALOS] "
                f"Trecho {indice} removido: "
                "começa após o fim do vídeo. "
                f"Início={inicio:.6f}s, "
                f"fim_real={duracao_video:.6f}s",
                flush=True,
            )
            continue

        duracao = fim_ajustado - inicio_ajustado

        if duracao <= 0:
            print(
                "[INTERVALOS] "
                f"Trecho {indice} removido: "
                "intervalo sem duração após ajuste.",
                flush=True,
            )
            continue

        trecho_final = fim >= duracao_video - 0.000001

        if trecho_final and duracao < duracao_quadro:
            print(
                "[INTERVALOS] "
                f"Resíduo final removido: "
                f"{duracao:.6f}s "
                f"(um quadro={duracao_quadro:.6f}s).",
                flush=True,
            )
            continue

        if (
            abs(inicio_ajustado - inicio) > 0.000001
            or abs(fim_ajustado - fim) > 0.000001
        ):
            print(
                "[INTERVALOS] "
                f"Trecho {indice} ajustado: "
                f"{inicio:.6f}-{fim:.6f}s "
                f"para "
                f"{inicio_ajustado:.6f}-"
                f"{fim_ajustado:.6f}s",
                flush=True,
            )

        resultado.append(
            (inicio_ajustado, fim_ajustado)
        )

    return resultado


# ============================================================
# CONCATENAÇÃO
# ============================================================

def _concatenar_lote(
    arquivos,
    saida,
    fps,
    possui_audio,
    pasta,
    identificador,
):
    """
    Concatena um lote de segmentos com recodificação
    e reconstrução dos timestamps.
    """
    if not arquivos:
        raise ValueError("Lote de segmentos vazio.")

    entradas = []

    for arquivo in arquivos:
        entradas.extend(["-i", str(arquivo)])

    filtros = []
    quantidade = len(arquivos)

    for i in range(quantidade):
        filtros.append(
            f"[{i}:v:0]"
            f"fps={fps},"
            "settb=AVTB,"
            "setpts=PTS-STARTPTS,"
            "format=yuv420p,"
            "setsar=1"
            f"[v{i}]"
        )

        if possui_audio:
            filtros.append(
                f"[{i}:a:0]"
                "aresample=48000:first_pts=0,"
                "asetpts=PTS-STARTPTS"
                f"[a{i}]"
            )

    if quantidade == 1:
        saida_video = "[v0]"
        saida_audio = "[a0]" if possui_audio else None

    else:
        entradas_concat = []

        for i in range(quantidade):
            entradas_concat.append(f"[v{i}]")

            if possui_audio:
                entradas_concat.append(f"[a{i}]")

        if possui_audio:
            filtros.append(
                "".join(entradas_concat)
                + f"concat=n={quantidade}:v=1:a=1"
                + "[vout][aout]"
            )
            saida_video = "[vout]"
            saida_audio = "[aout]"

        else:
            filtros.append(
                "".join(entradas_concat)
                + f"concat=n={quantidade}:v=1:a=0"
                + "[vout]"
            )
            saida_video = "[vout]"
            saida_audio = None

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
        saida_video,
    ]

    if possui_audio:
        cmd.extend(["-map", saida_audio])

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
        str(saida),
    ])

    executar(
        cmd,
        f"Concatenação {identificador}",
        Path(pasta) / f"concat_{identificador}.log",
    )

    if (
        not Path(saida).is_file()
        or Path(saida).stat().st_size == 0
    ):
        raise RuntimeError(
            f"Arquivo de concatenação vazio: {saida}"
        )

    _validar_duracoes(
        saida,
        possui_audio,
        tolerancia=1.0,
    )


def _concatenar_trechos(
    arquivos,
    saida,
    fps,
    possui_audio,
    pasta,
):
    """
    Concatena em lotes para evitar comandos
    excessivamente longos no Windows.
    """
    arquivos = list(arquivos)

    if not arquivos:
        raise ValueError("Nenhum trecho para concatenar.")

    tamanho_lote = 12
    rodada = 0

    while len(arquivos) > 1:
        rodada += 1
        novos_arquivos = []

        for indice in range(0, len(arquivos), tamanho_lote):
            grupo = arquivos[
                indice:indice + tamanho_lote
            ]

            if len(grupo) == 1:
                novos_arquivos.append(grupo[0])
                continue

            identificador = (
                f"r{rodada:02d}_"
                f"l{indice // tamanho_lote:03d}"
            )

            intermediario = (
                Path(pasta)
                / f"concat_{identificador}.mp4"
            )

            _concatenar_lote(
                grupo,
                intermediario,
                fps,
                possui_audio,
                pasta,
                identificador,
            )

            novos_arquivos.append(intermediario)

        arquivos = novos_arquivos

    final = arquivos[0]

    if final != Path(saida):
        shutil.copy2(final, saida)

    _validar_duracoes(
        saida,
        possui_audio,
        tolerancia=1.0,
    )


# ============================================================
# RENDERIZAÇÃO PRINCIPAL
# ============================================================

def renderizar_edicao(
    caminho_entrada,
    caminho_saida,
    cortes,
    ruido="nenhum",
    callback=None,
    transicao="Nenhuma",
    duracao_transicao=0.7,
    melhorar_audio_habilitado=True,
):
    """
    Renderiza o vídeo editado.

    Usa a duração real do fluxo de vídeo
    como limite dos trechos preservados.
    """
    origem = Path(caminho_entrada)
    destino = Path(caminho_saida)

    if not origem.is_file():
        raise FileNotFoundError(
            f"Vídeo de entrada não encontrado: {origem}"
        )

    info = analisar_video(origem)

    duracao_container = float(info["duracao"])
    duracao_video = _duracao_real_video(origem)

    if duracao_video <= 0:
        raise RuntimeError(
            "A duração do fluxo de vídeo é inválida."
        )

    fps = _fps_ffmpeg(info["fps"])
    possui_audio = bool(info["possui_audio"])

    print(
        "[RENDER] Iniciando renderização corrigida",
        flush=True,
    )

    print(
        f"[RENDER] Duração do contêiner: "
        f"{duracao_container:.6f}s",
        flush=True,
    )

    print(
        f"[RENDER] Fim real do vídeo: "
        f"{duracao_video:.6f}s",
        flush=True,
    )

    print(
        f"[RENDER] FPS: {fps}",
        flush=True,
    )

    # Validação dos cortes recebidos.
    intervalos = []

    for corte in cortes:
        if not isinstance(corte, dict):
            raise ValueError(
                "Cada corte precisa ser um objeto "
                "com inicio e fim."
            )

        inicio = float(corte["inicio"])
        fim = float(corte["fim"])

        if (
            not math.isfinite(inicio)
            or not math.isfinite(fim)
            or inicio < 0
            or fim > duracao_container + 0.1
            or fim <= inicio
        ):
            raise ValueError(
                f"Corte inválido: {corte}"
            )

        # Limita cortes à linha temporal do vídeo.
        if inicio >= duracao_video:
            print(
                "[CORTES] Corte ignorado por estar "
                "inteiramente após o fim do vídeo: "
                f"{inicio:.6f}-{fim:.6f}s",
                flush=True,
            )
            continue

        fim_ajustado = min(fim, duracao_video)

        if fim_ajustado > inicio:
            intervalos.append(
                (inicio, fim_ajustado)
            )

    # A função recebe a duração efetiva do vídeo,
    # e não a duração total do contêiner.
    manter = trechos_preservados(
        intervalos,
        duracao_video,
    )

    manter = _normalizar_intervalos(
        manter,
        duracao_video,
        fps,
    )

    if not manter:
        raise ValueError(
            "Os cortes removeriam todo o vídeo."
        )

    if len(manter) > MAX_TRECHOS:
        raise ValueError(
            "Trechos demais; reduza os cortes "
            "ou divida o vídeo."
        )

    duracao_transicao = validar_transicao(
        transicao,
        duracao_transicao,
    )

    if (
        transicao != "Nenhuma"
        and len(manter) > 1
        and duracao_transicao
        >= min(b - a for a, b in manter) - 0.08
    ):
        raise ValueError(
            "A transição é maior que um dos "
            "trechos preservados. "
            "Diminua sua duração."
        )

    filtro = filtro_ruido(ruido)

    if ruido != "nenhum" and not filtro:
        raise ValueError(
            "Nível de ruído inválido."
        )

    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"[RENDER] Trechos preservados: {len(manter)}",
        flush=True,
    )

    for indice, (inicio, fim) in enumerate(manter, 1):
        print(
            f"[RENDER] Trecho {indice}/{len(manter)} | "
            f"Início: {inicio:.6f}s | "
            f"Fim: {fim:.6f}s | "
            f"Duração: {fim - inicio:.6f}s",
            flush=True,
        )

    with tempfile.TemporaryDirectory(
        prefix="promptvideo_",
        dir=str(destino.parent),
    ) as pasta_temporaria:

        tmp = Path(pasta_temporaria)
        arquivos = []

        try:
            for i, (inicio, fim) in enumerate(manter, 1):

                if callback:
                    callback(
                        0.05 + 0.72 * (i - 1) / len(manter),
                        (
                            f"Codificando trecho {i} "
                            f"de {len(manter)}"
                        ),
                    )

                print(
                    f"[RENDER] Trecho {i}/{len(manter)} | "
                    f"Início: {inicio:.6f}s | "
                    f"Fim: {fim:.6f}s | "
                    f"Duração: {fim - inicio:.6f}s",
                    flush=True,
                )

                arquivo = (
                    tmp / f"trecho_{i:04d}.mp4"
                )

                duracao_trecho = fim - inicio

                filtros_video = (
                    f"fps={fps},"
                    "settb=AVTB,"
                    "setpts=PTS-STARTPTS,"
                    "format=yuv420p,"
                    "setsar=1"
                )

                cmd = [
                    ffmpeg_bin("ffmpeg"),
                    "-y",
                    "-hide_banner",
                    "-nostdin",
                    "-nostats",
                    "-threads",
                    str(THREADS_FFMPEG),
                    "-ss",
                    f"{inicio:.6f}",
                    "-i",
                    str(origem),
                    "-t",
                    f"{duracao_trecho:.6f}",
                    "-map",
                    "0:v:0",
                ]

                if possui_audio:
                    cmd.extend(["-map", "0:a:0"])
                else:
                    cmd.append("-an")

                cmd.extend([
                    "-vf",
                    filtros_video,
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
                    "-fps_mode:v",
                    "cfr",
                ])

                if possui_audio:
                    filtros_audio = []

                    if filtro:
                        filtros_audio.append(filtro)

                    filtros_audio.extend([
                        "aresample=48000:first_pts=0",
                        "asetpts=PTS-STARTPTS",
                    ])

                    cmd.extend([
                        "-af",
                        ",".join(filtros_audio),
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
                    "-avoid_negative_ts",
                    "make_zero",
                    str(arquivo),
                ])

                executar(
                    cmd,
                    f"Trecho {i}",
                    tmp / f"trecho_{i:04d}.log",
                )

                if (
                    not arquivo.is_file()
                    or arquivo.stat().st_size == 0
                ):
                    raise RuntimeError(
                        f"Trecho {i} vazio. "
                        f"Início={inicio:.6f}s, "
                        f"fim={fim:.6f}s, "
                        f"duração={duracao_trecho:.6f}s."
                    )

                try:
                    _validar_duracoes(
                        arquivo,
                        possui_audio,
                        tolerancia=1.0,
                    )

                except Exception as exc:
                    raise RuntimeError(
                        f"Falha na validação do trecho {i}. "
                        f"Início={inicio:.6f}s, "
                        f"fim={fim:.6f}s, "
                        f"duração={duracao_trecho:.6f}s. "
                        f"Detalhes: {exc}"
                    ) from exc

                arquivos.append(arquivo)

                if callback:
                    callback(
                        0.05 + 0.72 * i / len(manter),
                        (
                            f"Trecho {i} de "
                            f"{len(manter)} concluído"
                        ),
                    )

            parcial = tmp / "final.mp4"

            if (
                transicao != "Nenhuma"
                and len(arquivos) > 1
            ):
                if callback:
                    callback(
                        0.79,
                        "Aplicando transições entre cortes",
                    )

                unir_com_transicoes(
                    arquivos,
                    [b - a for a, b in manter],
                    parcial,
                    transicao,
                    duracao_transicao,
                    float(Fraction(fps)),
                    possui_audio,
                    tmp,
                )

                _validar_duracoes(
                    parcial,
                    possui_audio,
                    tolerancia=1.0,
                )

            else:
                if callback:
                    callback(
                        0.79,
                        "Unindo trechos com timestamps corrigidos",
                    )

                _concatenar_trechos(
                    arquivos,
                    parcial,
                    fps,
                    possui_audio,
                    tmp,
                )

            if (
                not parcial.is_file()
                or parcial.stat().st_size == 0
            ):
                raise RuntimeError(
                    "O vídeo intermediário está vazio."
                )

            if possui_audio and melhorar_audio_habilitado:
                aprimorado = (
                    tmp / "final_audio_melhorado.mp4"
                )

                if callback:
                    callback(
                        0.86,
                        "Melhorando áudio",
                    )

                melhorar_audio(
                    parcial,
                    aprimorado,
                )

                if (
                    not aprimorado.is_file()
                    or aprimorado.stat().st_size == 0
                ):
                    raise RuntimeError(
                        "Falha ao gerar o vídeo "
                        "com áudio melhorado."
                    )

                _validar_duracoes(
                    aprimorado,
                    possui_audio,
                    tolerancia=1.0,
                )

                os.replace(
                    aprimorado,
                    destino,
                )

            else:
                os.replace(
                    parcial,
                    destino,
                )

        except Exception:
            diagnosticos = (
                destino.parent / "diagnosticos_render"
            )

            diagnosticos.mkdir(
                parents=True,
                exist_ok=True,
            )

            for arquivo_log in tmp.glob("*.log"):
                shutil.copy2(
                    arquivo_log,
                    diagnosticos / arquivo_log.name,
                )

            for nome in (
                "final.mp4",
                "final_audio_melhorado.mp4",
            ):
                intermediario = tmp / nome

                if intermediario.is_file():
                    shutil.copy2(
                        intermediario,
                        diagnosticos / nome,
                    )

            raise

    if callback:
        callback(
            1.0,
            "Vídeo editado",
        )

    print(
        f"[RENDER] Concluído: {destino}",
        flush=True,
    )

    return destino
