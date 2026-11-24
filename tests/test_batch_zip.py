import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from promptvideo.core.batch import executar_lote


def simular_lote(base, nomes, nomes_srt=None):
    entradas = []
    resultados = []
    legendas = []

    for indice, nome in enumerate(nomes, 1):
        pasta = base / f"item_{indice}"
        pasta.mkdir()

        entrada = pasta / "entrada.mp4"
        entrada.write_bytes(b"entrada")
        entradas.append(str(entrada))

        saida = pasta / nome
        saida.write_bytes(f"video_{indice}".encode())
        resultados.append(saida)

        if nomes_srt is not None:
            srt = pasta / nomes_srt[indice - 1]
            srt.write_bytes(f"legenda_{indice}".encode())
            legendas.append(srt)

    propostas = [
        (f"video_{i:04d}", {"cortes": []})
        for i in range(1, len(nomes) + 1)
    ]

    with patch(
        "promptvideo.core.batch.SAIDAS", base
    ), patch(
        "promptvideo.core.batch.preparar_video",
        side_effect=propostas
    ), patch(
        "promptvideo.core.batch.aplicar_proposta",
        side_effect=[str(p) for p in resultados]
    ), patch(
        "promptvideo.core.batch.legendar_video",
        side_effect=[
            (str(v), str(s))
            for v, s in zip(resultados, legendas)
        ]
    ):
        pacote, registros = executar_lote(
            entradas,
            "edite",
            legendas=nomes_srt is not None
        )

    assert all(
        r["status"] == "concluido"
        for r in registros
    )

    return pacote, registros, resultados, legendas


@pytest.mark.parametrize(
    "nomes, esperados",
    [
        pytest.param(
            ["video_0001_editado.mp4",
             "video_0002_editado.mp4"],
            ["video_0001_editado.mp4",
             "video_0002_editado.mp4"],
            id="nomes-distintos"
        ),
        pytest.param(
            ["editado.mp4", "editado.mp4"],
            ["editado.mp4", "editado_2.mp4"],
            id="nomes-identicos"
        ),
        pytest.param(
            ["editado.mp4", "EDITADO.mp4"],
            ["editado.mp4", "EDITADO_2.mp4"],
            id="maiusculas-minusculas"
        ),
        pytest.param(
            ["editado.mp4", "editado_2.mp4",
             "editado.mp4"],
            ["editado.mp4", "editado_2.mp4",
             "editado_3.mp4"],
            id="sufixo-ocupado"
        )
    ]
)
def test_nomes_zip(tmp_path, nomes, esperados):
    pacote, registros, resultados, _ = simular_lote(
        tmp_path, nomes
    )

    with zipfile.ZipFile(pacote) as z:
        membros = z.namelist()

        assert len(membros) == len(esperados) + 1
        assert len(membros) == len({
            n.casefold() for n in membros
        })

        assert set(membros) == {
            "relatorio.json", *esperados
        }

        for indice, nome in enumerate(esperados, 1):
            assert z.read(nome) == (
                f"video_{indice}".encode()
            )

        assert z.testzip() is None

    assert [
        r["saida_zip"] for r in registros
    ] == esperados

    assert all(p.is_file() for p in resultados)


def test_colisao_legendas(tmp_path):
    pacote, registros, _, _ = simular_lote(
        tmp_path,
        ["editado.mp4", "editado.mp4"],
        ["legenda.srt", "legenda.srt"]
    )

    with zipfile.ZipFile(pacote) as z:
        assert z.read("legenda.srt") == b"legenda_1"
        assert z.read("legenda_2.srt") == b"legenda_2"

        assert len(z.namelist()) == 5
        assert z.testzip() is None

    assert registros[0]["srt_zip"] == "legenda.srt"
    assert registros[1]["srt_zip"] == "legenda_2.srt"


def test_correspondencia_relatorio(tmp_path):
    pacote, registros, resultados, legendas = (
        simular_lote(
            tmp_path,
            ["editado.mp4", "editado.mp4"],
            ["legenda.srt", "legenda.srt"]
        )
    )

    with zipfile.ZipFile(pacote) as z:
        relatorio = json.loads(
            z.read("relatorio.json")
        )

        assert relatorio["itens"] == registros

        for i, registro in enumerate(registros):
            assert Path(registro["saida"]) == resultados[i]
            assert Path(registro["srt"]) == legendas[i]

            assert z.read(registro["saida_zip"]) == (
                resultados[i].read_bytes()
            )

            assert z.read(registro["srt_zip"]) == (
                legendas[i].read_bytes()
            )


def test_nome_reservado_relatorio(tmp_path):
    pacote, registros, _, _ = simular_lote(
        tmp_path,
        ["editado.mp4"],
        ["RELATORIO.json"]
    )

    with zipfile.ZipFile(pacote) as z:
        relatorio = json.loads(
            z.read("relatorio.json")
        )

        assert relatorio["itens"] == registros

        assert z.read("RELATORIO_2.json") == (
            b"legenda_1"
        )

        assert len(z.namelist()) == 3

    assert registros[0]["srt_zip"] == (
        "RELATORIO_2.json"
    )


def test_falha_isolada_campos_zip(tmp_path):
    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    saida = tmp_path / "editado.mp4"

    a.write_bytes(b"a")
    b.write_bytes(b"b")
    saida.write_bytes(b"video")

    with patch(
        "promptvideo.core.batch.SAIDAS", tmp_path
    ), patch(
        "promptvideo.core.batch.preparar_video",
        side_effect=[
            RuntimeError("falha simulada"),
            ("video_0002", {"cortes": []})
        ]
    ), patch(
        "promptvideo.core.batch.aplicar_proposta",
        return_value=str(saida)
    ):
        pacote, registros = executar_lote(
            [str(a), str(b)], "edite"
        )

    assert registros[0]["status"] == "erro"
    assert registros[0]["saida_zip"] is None
    assert registros[0]["srt_zip"] is None

    assert registros[1]["status"] == "concluido"
    assert registros[1]["saida_zip"] == "editado.mp4"
    assert registros[1]["srt_zip"] is None

    with zipfile.ZipFile(pacote) as z:
        assert set(z.namelist()) == {
            "relatorio.json", "editado.mp4"
        }

        assert z.read("editado.mp4") == b"video"

        relatorio = json.loads(
            z.read("relatorio.json")
        )

        assert relatorio["itens"] == registros
