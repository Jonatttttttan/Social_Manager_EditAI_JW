"""Pipeline de exportacao com revisao de legendas."""

from pathlib import Path

from promptvideo.features.audio import transcrever

from promptvideo.features.subtitles import (
    validar_aparencia,
    _chunks,
)

from promptvideo.features.background_music import (
    adicionar_musica,
    escolher_musica,
    validar_volume,
)

from promptvideo.features.sound_effects import (
    aplicar_efeitos,
)

from promptvideo.features.video_filters import (
    aplicar_filtro_video,
)

from promptvideo.features.subtitle_session import (
    criar_sessao_revisao,
    exportar_revisao,
)


def exportar_com_revisao(
    video_editado,
    estilo="Tradicional",
    visual="Cl\u00e1ssica",
    tamanho=100,
    posicao="Inferior",
    trilha="Sem m\u00fasica",
    arquivo_musica=None,
    volume_musica=20,
    manter_audio=True,
    fade_musica=True,
    eventos_efeitos=None,
    filtro_video="Original",
    intensidade_filtro=60,
    brilho_filtro=0,
    contraste_filtro=0,
    callback=None,
    transicoes=None
):
    """Exporta um video com legendas automaticas revisaveis."""

    def progresso(pct, mensagem):
        if callback:
            callback(pct, mensagem)

    from promptvideo.features.subtitle_storage import (
        normalizar_config_transicoes,
    )

    transicoes = normalizar_config_transicoes(transicoes)

    caminho = Path(video_editado).resolve()

    if not caminho.is_file():
        raise FileNotFoundError(caminho)

    if estilo not in ("Tradicional", "Din\u00e2mica"):
        raise ValueError("Modo de legenda invalido.")

    visual, tamanho, posicao = validar_aparencia(
        visual, tamanho, posicao
    )

    escolher_musica(trilha, arquivo_musica)
    validar_volume(volume_musica)

    progresso(0.05, "Transcrevendo audio original")

    segmentos = transcrever(caminho)

    if not segmentos or not _chunks(segmentos):
        raise ValueError(
            "Nenhuma fala identificada para legendagem."
        )

    progresso(0.45, "Preparando musica de fundo")

    caminho = adicionar_musica(
        caminho,
        trilha,
        arquivo_musica,
        volume_musica,
        manter_audio,
        fade_musica,
        callback=lambda msg: progresso(0.50, msg)
    )

    if eventos_efeitos:
        progresso(0.55, "Preparando efeitos sonoros")

        caminho = aplicar_efeitos(
            caminho,
            eventos_efeitos,
            callback=lambda msg: progresso(0.58, msg)
        )

    progresso(0.60, "Preparando filtro visual")

    caminho = aplicar_filtro_video(
        caminho,
        filtro_video,
        intensidade_filtro,
        brilho_filtro,
        contraste_filtro,
        callback=lambda msg: progresso(0.65, msg)
    )

    progresso(0.70, "Preservando video base")

    identificador = criar_sessao_revisao(
        caminho,
        segmentos,
        estilo,
        visual,
        tamanho,
        posicao,
        transicoes=transicoes
    )

    progresso(0.80, "Gerando video legendado")

    mp4, srt = exportar_revisao(
        identificador,
        callback=lambda pct, msg: progresso(
            0.80 + 0.20 * pct,
            msg
        )
    )

    progresso(1.0, "Video pronto para revisao")

    return mp4, srt, identificador
