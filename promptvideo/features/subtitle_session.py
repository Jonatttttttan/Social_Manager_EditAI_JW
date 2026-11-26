"""Gerenciamento local das sessoes de revisao de legendas."""

import re
import shutil
import hashlib

from pathlib import Path
from uuid import uuid4

from promptvideo.config import BASE

from promptvideo.features.subtitle_storage import (
    salvar_transcricao_original,
    carregar_transcricao,
    salvar_transcricao_corrigida,
)

from promptvideo.features.subtitle_renderer import (
    renderizar_legendas_salvas,
)


def _raiz_revisoes():
    raiz = BASE / "revisoes_legendas"
    raiz.mkdir(parents=True, exist_ok=True)
    return raiz.resolve()


def _sha256(caminho):
    digest = hashlib.sha256()

    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(
            lambda: arquivo.read(1024 * 1024), b""
        ):
            digest.update(bloco)

    return digest.hexdigest()


def _pasta_sessao(identificador):
    if not isinstance(identificador, str):
        raise ValueError("Identificador invalido.")

    if not re.fullmatch(r"[a-f0-9]{32}", identificador):
        raise ValueError("Identificador invalido.")

    raiz = _raiz_revisoes()
    pasta = (raiz / identificador).resolve()

    if pasta.parent != raiz:
        raise ValueError("Diretorio de revisao invalido.")

    if not pasta.is_dir():
        raise FileNotFoundError("Sessao nao encontrada.")

    return pasta


def criar_sessao_revisao(
    video_base,
    segmentos,
    estilo,
    visual,
    tamanho,
    posicao,
    transicoes=None
):
    origem = Path(video_base).resolve()

    if not origem.is_file():
        raise FileNotFoundError(origem)

    if origem.suffix.lower() != ".mp4":
        raise ValueError("O video base deve estar em MP4.")

    if origem.stat().st_size == 0:
        raise ValueError("Video base vazio.")

    identificador = uuid4().hex
    pasta = _raiz_revisoes() / identificador

    pasta.mkdir(exist_ok=False)

    try:
        copia = pasta / "video_base.mp4"

        shutil.copy2(origem, copia)

        hash_origem = _sha256(origem)
        hash_copia = _sha256(copia)

        if hash_origem != hash_copia:
            raise RuntimeError(
                "Falha na integridade do video base."
            )

        salvar_transcricao_original(
            pasta / "legendas_originais.json",
            segmentos,
            estilo,
            visual,
            tamanho,
            posicao,
            transicoes=transicoes
        )

        (pasta / "video_base.sha256").write_text(
            hash_copia,
            encoding="ascii"
        )

    except Exception:
        shutil.rmtree(pasta)
        raise

    return identificador


def carregar_sessao_revisao(identificador):
    pasta = _pasta_sessao(identificador)

    video = pasta / "video_base.mp4"
    original = pasta / "legendas_originais.json"
    corrigida = pasta / "legendas_corrigidas.json"
    hash_path = pasta / "video_base.sha256"

    if not video.is_file() or not hash_path.is_file():
        raise FileNotFoundError(
            "Arquivos da sessao incompletos."
        )

    hash_esperado = hash_path.read_text(
        encoding="ascii"
    ).strip()

    if _sha256(video) != hash_esperado:
        raise RuntimeError(
            "O video base foi alterado."
        )

    dados_originais = carregar_transcricao(original)

    if dados_originais["tipo"] != "original":
        raise ValueError("Transcricao original invalida.")

    dados_corrigidos = None

    if corrigida.is_file():
        dados_corrigidos = carregar_transcricao(corrigida)

        if dados_corrigidos["tipo"] != "corrigida":
            raise ValueError("Transcricao corrigida invalida.")

    return {
        "identificador": identificador,
        "pasta": str(pasta),
        "video_base": str(video),
        "arquivo_original": str(original),
        "arquivo_corrigido": str(corrigida),
        "original": dados_originais,
        "corrigida": dados_corrigidos
    }


def salvar_revisao(identificador, textos):
    sessao = carregar_sessao_revisao(identificador)

    return salvar_transcricao_corrigida(
        sessao["arquivo_original"],
        sessao["arquivo_corrigido"],
        textos
    )


def exportar_revisao(identificador, callback=None):
    sessao = carregar_sessao_revisao(identificador)

    arquivo_json = (
        sessao["arquivo_corrigido"]
        if sessao["corrigida"] is not None
        else sessao["arquivo_original"]
    )

    return renderizar_legendas_salvas(
        sessao["video_base"],
        arquivo_json,
        callback=callback
    )


def restaurar_revisao(identificador):
    sessao = carregar_sessao_revisao(identificador)

    Path(sessao["arquivo_corrigido"]).unlink(
        missing_ok=True
    )

    return sessao["original"]["segmentos"]
