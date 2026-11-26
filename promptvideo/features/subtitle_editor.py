"""Motor de revisao de legendas do EditAI."""

import math
from copy import deepcopy


def _normalizar_texto(texto):
    if not isinstance(texto, str):
        raise ValueError("O texto da legenda deve ser uma string.")

    texto = " ".join(texto.split())

    if not texto:
        raise ValueError("O texto da legenda nao pode ficar vazio.")

    return texto


def _validar_intervalo(inicio, fim):
    inicio = float(inicio)
    fim = float(fim)

    if not math.isfinite(inicio) or not math.isfinite(fim):
        raise ValueError("Intervalo temporal invalido.")

    if inicio < 0 or fim <= inicio:
        raise ValueError("Intervalo temporal invalido.")

    return inicio, fim


def corrigir_segmento(segmento, novo_texto):
    """Corrige uma legenda sem modificar o segmento original."""

    if not isinstance(segmento, dict):
        raise ValueError("Segmento invalido.")

    texto = _normalizar_texto(novo_texto)
    inicio, fim = _validar_intervalo(
        segmento["inicio"], segmento["fim"]
    )

    resultado = deepcopy(segmento)

    original = " ".join(
        str(segmento.get("texto", "")).split()
    )

    if texto == original:
        return resultado

    resultado["texto"] = texto

    palavras_novas = texto.split()
    palavras_originais = segmento.get("palavras") or []

    if len(palavras_novas) == len(palavras_originais):
        novas = []

        for palavra, anterior in zip(
            palavras_novas, palavras_originais
        ):
            a, b = _validar_intervalo(
                anterior["inicio"], anterior["fim"]
            )

            registro = deepcopy(anterior)
            registro["texto"] = palavra
            novas.append(registro)

        resultado["palavras"] = novas

    else:
        quantidade = len(palavras_novas)
        intervalo = (fim - inicio) / quantidade

        resultado["palavras"] = [
            {
                "inicio": inicio + k * intervalo,
                "fim": (
                    fim if k == quantidade - 1
                    else inicio + (k + 1) * intervalo
                ),
                "texto": palavra
            }
            for k, palavra in enumerate(palavras_novas)
        ]

    return resultado


def corrigir_segmentos(segmentos, textos):
    """Aplica correcoes preservando a quantidade de segmentos."""

    if not isinstance(segmentos, (list, tuple)):
        raise ValueError("Lista de segmentos invalida.")

    if not isinstance(textos, (list, tuple)):
        raise ValueError("Lista de textos invalida.")

    if not segmentos:
        raise ValueError("Nenhuma legenda disponivel.")

    if len(segmentos) != len(textos):
        raise ValueError(
            "A quantidade de segmentos deve ser preservada."
        )

    return [
        corrigir_segmento(segmento, texto)
        for segmento, texto in zip(segmentos, textos)
    ]


def restaurar_segmentos(segmentos_originais):
    """Retorna uma copia independente das legendas originais."""

    return deepcopy(segmentos_originais)
