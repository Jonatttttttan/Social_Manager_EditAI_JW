"""Armazenamento de dados para revisao de legendas."""

import json
import os
import tempfile
from pathlib import Path
from copy import deepcopy

from promptvideo.features.subtitle_editor import corrigir_segmentos


VERSAO_FORMATO = 1


def _gravar_json(caminho, dados, sobrescrever=False):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    conteudo = json.dumps(
        dados,
        ensure_ascii=False,
        indent=2,
        allow_nan=False
    )

    if not sobrescrever:
        with caminho.open("x", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)

        return str(caminho)

    temporario = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=".legendas_",
            suffix=".tmp",
            delete=False
        ) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())

        os.replace(temporario, caminho)

    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()

    return str(caminho)


def normalizar_config_transicoes(transicoes=None):
    from promptvideo.features.edge_transitions import (
        validar_transicao_extremidade,
    )

    if transicoes is None:
        transicoes = {}

    if not isinstance(transicoes, dict):
        raise ValueError("Configuracao de transicoes invalida.")

    permitidas = {
        "abertura",
        "duracao_abertura",
        "encerramento",
        "duracao_encerramento",
    }

    if set(transicoes) - permitidas:
        raise ValueError("Campos de transicoes desconhecidos.")

    abertura = transicoes.get("abertura", "Nenhuma")
    encerramento = transicoes.get("encerramento", "Nenhuma")

    a = validar_transicao_extremidade(
        abertura,
        transicoes.get("duracao_abertura", 1.0)
    )

    b = validar_transicao_extremidade(
        encerramento,
        transicoes.get("duracao_encerramento", 1.0)
    )

    return {
        "abertura": abertura,
        "duracao_abertura": a if a > 0 else 1.0,
        "encerramento": encerramento,
        "duracao_encerramento": b if b > 0 else 1.0,
    }


def salvar_transcricao_original(
    caminho,
    segmentos,
    estilo,
    visual,
    tamanho,
    posicao,
    transicoes=None
):
    if not isinstance(segmentos, list) or not segmentos:
        raise ValueError("Nenhuma transcricao disponivel.")

    textos = [segmento["texto"] for segmento in segmentos]

    corrigir_segmentos(segmentos, textos)

    dados = {
        "versao_formato": VERSAO_FORMATO,
        "tipo": "original",
        "configuracoes": {
            "estilo": estilo,
            "visual": visual,
            "tamanho": tamanho,
            "posicao": posicao,
            "transicoes": normalizar_config_transicoes(transicoes)
        },
        "segmentos": deepcopy(segmentos)
    }

    return _gravar_json(
        caminho,
        dados,
        sobrescrever=False
    )


def carregar_transcricao(caminho):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError(caminho)

    dados = json.loads(
        caminho.read_text(encoding="utf-8-sig")
    )

    if not isinstance(dados, dict):
        raise ValueError("Formato de transcricao invalido.")

    if dados.get("versao_formato") != VERSAO_FORMATO:
        raise ValueError("Versao de transcricao incompativel.")

    if dados.get("tipo") not in ("original", "corrigida"):
        raise ValueError("Tipo de transcricao invalido.")

    segmentos = dados.get("segmentos")

    if not isinstance(segmentos, list) or not segmentos:
        raise ValueError("Transcricao sem segmentos validos.")

    configuracoes = dados.get("configuracoes")

    if not isinstance(configuracoes, dict):
        raise ValueError("Configuracoes invalidas.")

    obrigatorias = {
        "estilo", "visual", "tamanho", "posicao"
    }

    if not obrigatorias.issubset(configuracoes):
        raise ValueError("Configuracoes incompletas.")

    corrigir_segmentos(
        segmentos,
        [segmento["texto"] for segmento in segmentos]
    )

    if "transicoes" in configuracoes:
        configuracoes["transicoes"] = normalizar_config_transicoes(
            configuracoes["transicoes"]
        )

    return dados


def salvar_transcricao_corrigida(
    caminho_original,
    caminho_corrigido,
    textos
):
    original = Path(caminho_original).resolve()
    corrigido = Path(caminho_corrigido).resolve()

    if original == corrigido:
        raise ValueError(
            "A transcricao original nao pode ser sobrescrita."
        )

    if corrigido.exists() and os.path.samefile(original, corrigido):
        raise ValueError(
            "A transcricao original nao pode ser sobrescrita."
        )

    dados = carregar_transcricao(original)

    if dados["tipo"] != "original":
        raise ValueError("Utilize a transcricao original.")

    dados["segmentos"] = corrigir_segmentos(
        dados["segmentos"],
        textos
    )

    dados["tipo"] = "corrigida"

    return _gravar_json(
        corrigido,
        dados,
        sobrescrever=True
    )
