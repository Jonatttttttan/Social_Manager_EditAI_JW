"""Controladores da interface de revisao de legendas."""

import html
import gradio as gr

from promptvideo.features.subtitle_session import (
    carregar_sessao_revisao,
    salvar_revisao,
    exportar_revisao,
)

from promptvideo.features.subtitle_editor import (
    corrigir_segmentos,
)


def _formatar_tempo(segundos):
    ms = round(float(segundos) * 1000)

    horas, ms = divmod(ms, 3600000)
    minutos, ms = divmod(ms, 60000)
    segundos, ms = divmod(ms, 1000)

    return (
        f"{horas:02d}:{minutos:02d}:"
        f"{segundos:02d}.{ms:03d}"
    )


def _montar_linhas(segmentos):
    return [
        [
            str(i + 1),
            _formatar_tempo(segmento["inicio"]),
            _formatar_tempo(segmento["fim"]),
            segmento["texto"]
        ]
        for i, segmento in enumerate(segmentos)
    ]


def carregar_editor_legendas(identificador):
    """Carrega as legendas da edicao atual."""

    if not identificador:
        return (
            gr.update(visible=False),
            [],
            ""
        )

    try:
        sessao = carregar_sessao_revisao(
            identificador
        )

        dados = (
            sessao["corrigida"]
            or sessao["original"]
        )

        linhas = _montar_linhas(
            dados["segmentos"]
        )

        return (
            gr.update(visible=True),
            linhas,
            f"**{len(linhas)} segmentos disponiveis para revisao.**"
        )

    except Exception as erro:
        return (
            gr.update(visible=True),
            [],
            "Falha ao carregar legendas: "
            + html.escape(str(erro))
        )


def _extrair_textos(linhas, segmentos):
    """Valida a tabela sem permitir alterar os tempos."""

    if hasattr(linhas, "values"):
        linhas = linhas.values.tolist()

    if not isinstance(linhas, (list, tuple)):
        raise ValueError("Tabela de legendas invalida.")

    esperadas = _montar_linhas(segmentos)

    if len(linhas) != len(esperadas):
        raise ValueError(
            "A quantidade de legendas deve ser preservada."
        )

    textos = []

    for i, (linha, esperada) in enumerate(
        zip(linhas, esperadas), 1
    ):
        if not isinstance(linha, (list, tuple)):
            raise ValueError(f"Legenda {i} invalida.")

        if len(linha) != 4:
            raise ValueError(f"Legenda {i} incompleta.")

        if [str(v) for v in linha[:3]] != esperada[:3]:
            raise ValueError(
                f"Legenda {i}: nao altere o numero "
                "nem os intervalos de tempo."
            )

        texto = linha[3]

        if not isinstance(texto, str) or not texto.strip():
            raise ValueError(
                f"Legenda {i}: o texto nao pode ficar vazio."
            )

        textos.append(texto)

    corrigir_segmentos(segmentos, textos)

    return textos


def restaurar_editor_legendas(identificador):
    """Restaura os textos na tabela, sem reexportar."""

    if not identificador:
        raise gr.Error("Nenhuma sessao de revisao ativa.")

    try:
        sessao = carregar_sessao_revisao(
            identificador
        )

        linhas = _montar_linhas(
            sessao["original"]["segmentos"]
        )

        return (
            linhas,
            "Textos originais restaurados na tabela. "
            "Gere o video para aplicar as alteracoes."
        )

    except Exception as erro:
        raise gr.Error(str(erro)) from erro


def reexportar_editor_legendas(
    identificador,
    linhas,
    progress=gr.Progress()
):
    """Gera uma nova exportacao com os textos corrigidos."""

    from promptvideo.licensing import ensure_valid

    ensure_valid()

    if not identificador:
        raise gr.Error("Nenhuma sessao de revisao ativa.")

    try:
        progress(
            0.02,
            desc="Validando legendas"
        )

        sessao = carregar_sessao_revisao(
            identificador
        )

        textos = _extrair_textos(
            linhas,
            sessao["original"]["segmentos"]
        )

        salvar_revisao(
            identificador,
            textos
        )

        progress(
            0.10,
            desc="Preparando nova exportacao"
        )

        mp4, srt = exportar_revisao(
            identificador,
            callback=lambda pct, msg: progress(
                0.10 + 0.90 * pct,
                desc=msg
            )
        )

        return (
            gr.update(value=mp4, visible=True),
            gr.update(value=mp4, visible=True),
            gr.update(value=srt, visible=True),
            "**Video corrigido com sucesso!** "
            "A exportacao anterior foi preservada."
        )

    except Exception as erro:
        raise gr.Error(str(erro)) from erro
