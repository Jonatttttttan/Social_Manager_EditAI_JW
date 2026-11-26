import itertools
import pytest

from promptvideo.features.edge_transitions import (
    TRANSICOES_EXTREMIDADES,
    validar_transicao_extremidade,
    planejar_transicoes,
    construir_filtros_transicoes,
)


def test_catalogo_transicoes():
    assert len(TRANSICOES_EXTREMIDADES) == 9
    assert len(set(TRANSICOES_EXTREMIDADES)) == 9
    assert "Nenhuma" in TRANSICOES_EXTREMIDADES


def test_sem_transicoes():
    plano = planejar_transicoes(30)
    assert plano["ativo"] is False
    assert plano["duracao_trecho_livre"] == 30
    assert construir_filtros_transicoes(plano) == ""


def test_abertura_independente():
    plano = planejar_transicoes(30, "Fade preto", 1)
    assert plano["abertura"]["ativo"]
    assert not plano["encerramento"]["ativo"]
    assert plano["abertura"]["inicio"] == 0
    assert plano["abertura"]["fim"] == 1


def test_encerramento_independente():
    plano = planejar_transicoes(
        30, encerramento="Fade branco",
        duracao_encerramento=2
    )
    assert not plano["abertura"]["ativo"]
    assert plano["encerramento"]["ativo"]
    assert plano["encerramento"]["inicio"] == 28
    assert plano["encerramento"]["fim"] == 30


def test_video_curto():
    plano = planejar_transicoes(
        1, "Fade preto", 3, "Fade branco", 3
    )
    assert plano["duracoes_ajustadas"]
    assert plano["duracao_trecho_livre"] == pytest.approx(0.2)
    assert plano["abertura"]["fim"] <= plano["encerramento"]["inicio"]


@pytest.mark.parametrize(
    "duracao",
    [0, -1, 0.1, 3.1, float("nan"),
     float("inf"), True, None, "invalido"]
)
def test_duracoes_invalidas(duracao):
    with pytest.raises(ValueError):
        validar_transicao_extremidade("Fade preto", duracao)


@pytest.mark.parametrize(
    "duracao",
    [0, -1, float("nan"), float("inf"), True, None]
)
def test_duracao_video_invalida(duracao):
    with pytest.raises(ValueError):
        planejar_transicoes(duracao)


def test_transicao_desconhecida():
    with pytest.raises(ValueError):
        validar_transicao_extremidade("Inexistente", 1)


@pytest.mark.parametrize(
    "abertura,encerramento",
    list(itertools.product(
        TRANSICOES_EXTREMIDADES, repeat=2
    ))
)
def test_combinacoes_transicoes(abertura, encerramento):
    plano = planejar_transicoes(
        30, abertura, 1, encerramento, 1
    )

    filtros = construir_filtros_transicoes(plano)

    ativo = abertura != "Nenhuma" or encerramento != "Nenhuma"

    assert plano["ativo"] == ativo
    assert bool(filtros) == ativo

    assert plano["abertura"]["fim"] <= plano["encerramento"]["inicio"]

    assert plano["duracao_trecho_livre"] >= 0

    assert (
        plano["abertura"]["duracao"]
        + plano["encerramento"]["duracao"]
        + plano["duracao_trecho_livre"]
    ) == pytest.approx(30)
