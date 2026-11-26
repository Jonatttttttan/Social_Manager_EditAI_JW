import math

TRANSICOES_EXTREMIDADES = (
    "Nenhuma",
    "Fade preto",
    "Fade branco",
    "Desfoque",
    "Zoom",
    "Deslizar horizontal",
    "Deslizar vertical",
    "Cortina circular",
    "Cortina horizontal",
)

DURACAO_MINIMA = 0.2
DURACAO_MAXIMA = 3.0
FRACAO_MAXIMA_VIDEO = 0.8


def validar_transicao_extremidade(nome, duracao=1.0):
    if nome not in TRANSICOES_EXTREMIDADES:
        raise ValueError("Transicao desconhecida.")

    if nome == "Nenhuma":
        return 0.0

    if isinstance(duracao, bool):
        raise ValueError("Duracao invalida.")

    try:
        segundos = float(duracao)
    except (ValueError, TypeError):
        raise ValueError("Duracao invalida.") from None

    if not math.isfinite(segundos):
        raise ValueError("Duracao invalida.")

    if not DURACAO_MINIMA <= segundos <= DURACAO_MAXIMA:
        raise ValueError(
            "A duracao deve estar entre 0.2 e 3 segundos."
        )

    return segundos


def planejar_transicoes(
    duracao_video,
    abertura="Nenhuma",
    duracao_abertura=1.0,
    encerramento="Nenhuma",
    duracao_encerramento=1.0,
):
    if isinstance(duracao_video, bool):
        raise ValueError("Duracao do video invalida.")

    try:
        total = float(duracao_video)
    except (ValueError, TypeError):
        raise ValueError("Duracao do video invalida.") from None

    if not math.isfinite(total) or total <= 0:
        raise ValueError("Duracao do video invalida.")

    a = validar_transicao_extremidade(
        abertura, duracao_abertura
    )

    b = validar_transicao_extremidade(
        encerramento, duracao_encerramento
    )

    solicitado = a + b
    limite = total * FRACAO_MAXIMA_VIDEO

    fator = (
        min(1.0, limite / solicitado)
        if solicitado > 0
        else 1.0
    )

    a *= fator
    b *= fator

    return {
        "duracao_video": total,
        "abertura": {
            "nome": abertura,
            "ativo": a > 0,
            "inicio": 0.0,
            "fim": a,
            "duracao": a,
        },
        "encerramento": {
            "nome": encerramento,
            "ativo": b > 0,
            "inicio": total - b,
            "fim": total,
            "duracao": b,
        },
        "duracao_trecho_livre": total - a - b,
        "duracoes_ajustadas": fator < 1.0,
        "ativo": solicitado > 0,
    }

def _numero_ffmpeg(valor):
    return f"{float(valor):.9f}"


def _filtro_fade(transicao, abertura):
    cores = {
        "Fade preto": "black",
        "Fade branco": "white",
    }

    nome = transicao["nome"]

    if nome not in cores:
        raise ValueError("Efeito ainda nao implementado.")

    tipo = "in" if abertura else "out"

    inicio = _numero_ffmpeg(transicao["inicio"])
    duracao = _numero_ffmpeg(transicao["duracao"])
    cor = cores[nome]

    return (
        f"fade=t={tipo}:st={inicio}:"
        f"d={duracao}:color={cor}"
    )


def _intensidade_transicao(transicao, abertura, tempo):
    inicio = _numero_ffmpeg(transicao["inicio"])
    duracao = _numero_ffmpeg(transicao["duracao"])

    progresso = (
        f"clip(({tempo}-{inicio})/{duracao},0,1)"
    )

    if abertura:
        return f"(1-{progresso})"

    return progresso


def _filtro_geometrico(transicao, abertura):
    nome = transicao["nome"]

    q = _intensidade_transicao(
        transicao, abertura, "T"
    )

    expressoes = []

    for canal, funcao, preto in (
        ("lum", "lum", 16),
        ("cb", "cb", 128),
        ("cr", "cr", 128),
    ):
        original = f"{funcao}(X,Y)"

        if nome == "Zoom":
            escala = f"(1+0.5*{q})"

            x = f"((X-W/2)/{escala}+W/2)"
            y = f"((Y-H/2)/{escala}+H/2)"

            expr = f"{funcao}({x},{y})"

        elif nome == "Deslizar horizontal":
            x = f"(X-W*{q})"

            expr = (
                f"if(lt({x},0),"
                f"{preto},{funcao}({x},Y))"
            )

        elif nome == "Deslizar vertical":
            y = f"(Y-H*{q})"

            expr = (
                f"if(lt({y},0),"
                f"{preto},{funcao}(X,{y}))"
            )

        elif nome == "Cortina circular":
            distancia = (
                "sqrt(pow((X-W/2)/W,2)"
                "+pow((Y-H/2)/H,2))"
            )

            raio = f"(0.71*(1-{q}))"

            expr = (
                f"if(lte({q},0),{original},"
                f"if(gte({q},1),{preto},"
                f"if(lte({distancia},{raio}),"
                f"{original},{preto})))"
            )

        elif nome == "Cortina horizontal":
            limite = f"(W*(1-{q}))"

            expr = (
                f"if(lt(X,{limite}),"
                f"{original},{preto})"
            )

        else:
            raise ValueError(
                "Efeito geometrico desconhecido."
            )

        expressoes.append(
            f"{canal}='{expr}'"
        )

    return (
        "format=yuv420p,geq="
        + ":".join(expressoes)
    )


def _filtro_desfoque(transicao, abertura, indice):
    q = _intensidade_transicao(
        transicao, abertura, "T"
    )

    original = f"edge_original_{indice}"
    copia = f"edge_copia_{indice}"
    blur = f"edge_blur_{indice}"

    return (
        f"split=2[{original}][{copia}];"
        f"[{copia}]gblur=sigma=15[{blur}];"
        f"[{original}][{blur}]"
        f"blend=all_expr='A*(1-{q})+B*{q}'"
    )


def construir_filtros_transicoes(plano):
    filtros = []

    for indice, chave in enumerate(
        ("abertura", "encerramento")
    ):
        transicao = plano[chave]

        if not transicao["ativo"]:
            continue

        nome = transicao["nome"]
        abertura = chave == "abertura"

        if nome in ("Fade preto", "Fade branco"):
            filtro = _filtro_fade(
                transicao, abertura
            )

        elif nome == "Desfoque":
            filtro = _filtro_desfoque(
                transicao, abertura, indice
            )

        else:
            filtro = _filtro_geometrico(
                transicao, abertura
            )

        filtros.append(filtro)

    return ",".join(filtros)


def aplicar_transicoes_extremidades(
    video,
    abertura="Nenhuma",
    duracao_abertura=1.0,
    encerramento="Nenhuma",
    duracao_encerramento=1.0,
    callback=None,
):
    import os
    import subprocess
    import tempfile
    from pathlib import Path
    from uuid import uuid4

    from promptvideo.core.media import (
        analisar_video,
        ffmpeg_bin,
    )

    from promptvideo.features.subtitles import (
        _flags,
        _log_dir,
    )

    caminho = Path(video).resolve()

    if not caminho.is_file():
        raise FileNotFoundError(caminho)

    if caminho.suffix.lower() != ".mp4":
        raise ValueError("O video deve estar em MP4.")

    if caminho.stat().st_size == 0:
        raise ValueError("Video vazio.")

    validar_transicao_extremidade(
        abertura, duracao_abertura
    )

    validar_transicao_extremidade(
        encerramento, duracao_encerramento
    )

    if abertura == encerramento == "Nenhuma":
        return str(caminho)

    info = analisar_video(caminho)

    plano = planejar_transicoes(
        info["duracao"],
        abertura,
        duracao_abertura,
        encerramento,
        duracao_encerramento,
    )

    filtros = construir_filtros_transicoes(plano)

    if not filtros:
        return str(caminho)

    filtros = "setpts=PTS-STARTPTS," + filtros

    if callback:
        callback("Preparando transicoes")

    if plano["duracoes_ajustadas"] and callback:
        callback(
            "Duracoes ajustadas ao tamanho do video"
        )

    log_path = _log_dir() / (
        "transicoes_extremidades_"
        + uuid4().hex
        + ".log"
    )

    with tempfile.TemporaryDirectory(
        prefix=".transicoes_",
        dir=caminho.parent,
    ) as pasta:

        temporario = Path(pasta) / "resultado.mp4"

        cmd = [
            ffmpeg_bin("ffmpeg"),
            "-y",
            "-hide_banner",
            "-nostdin",
            "-nostats",
            "-i", str(caminho),
            "-map", "0:v:0",
            "-map", "0:a?",
            "-vf", filtros,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(temporario),
        ]

        if callback:
            callback("Renderizando transicoes")

        with log_path.open(
            "w",
            encoding="utf-8",
            errors="replace",
        ) as log:

            log.write(
                subprocess.list2cmdline(cmd) + "\n"
            )
            log.flush()

            processo = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=log,
                creationflags=_flags(),
            )

        if processo.returncode != 0:
            raise RuntimeError(
                "Falha nas transicoes. Log: "
                + str(log_path)
            )

        if not temporario.is_file():
            raise RuntimeError(
                "Video com transicoes nao gerado."
            )

        if temporario.stat().st_size == 0:
            raise RuntimeError(
                "Video com transicoes vazio."
            )

        resultado = analisar_video(temporario)

        duracao_original = float(info["duracao"])
        duracao_final = float(resultado["duracao"])

        if not math.isfinite(duracao_final):
            raise RuntimeError("Duracao final invalida.")

        if duracao_final <= 0:
            raise RuntimeError("Duracao final invalida.")

        diferenca = abs(
            duracao_original - duracao_final
        )

        if diferenca > 0.15:
            raise RuntimeError(
                "Duracao alterada pelas transicoes."
            )

        for chave in ("largura", "altura"):
            if resultado[chave] != info[chave]:
                raise RuntimeError(
                    "Resolucao do video alterada."
                )

        if bool(resultado.get("possui_audio")) != bool(
            info.get("possui_audio")
        ):
            raise RuntimeError(
                "Estrutura de audio alterada."
            )

        os.replace(temporario, caminho)

    if callback:
        callback("Transicoes aplicadas com sucesso")

    return str(caminho)
