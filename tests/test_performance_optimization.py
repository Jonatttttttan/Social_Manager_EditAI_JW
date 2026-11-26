import hashlib

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from promptvideo.core.memory_manager import (
    deve_liberar_whisper
)

from promptvideo.core.fast_path import (
    tentar_copia_direta
)

from promptvideo.features import audio


@pytest.mark.parametrize(
    "total,livre,esperado",
    [
        (4, 2, True),
        (8, 5, True),
        (8.5, 5, True),
        (16, 1, True),
        (16, 3.19, True),
        (16, 3.2, False),
        (16, 6, False),
        (32, 3, True),
        (32, 15, False),
        (64, 5, True),
        (64, 30, False),
        (0, 0, True),
        (16, -1, True),
        (8, 10, True),
        (float("inf"), 4, True),
        (16, float("nan"), True)
    ]
)
def test_politica_memoria(total, livre, esperado):

    liberar, _ = deve_liberar_whisper({
        "ram_total_gb": total,
        "ram_disponivel_gb": livre
    })

    assert liberar == esperado


def test_memoria_desconhecida():

    with patch(
        "promptvideo.core.memory_manager.consultar_memoria",
        return_value=None
    ):
        liberar, _ = deve_liberar_whisper()

    assert liberar


def sha256(arquivo):

    return hashlib.sha256(
        arquivo.read_bytes()
    ).hexdigest()


def test_copia_direta_preserva_conteudo(tmp_path):

    origem = tmp_path / "origem.mp4"
    destino = tmp_path / "destino.mp4"

    origem.write_bytes(b"conteudo original")

    assinatura = sha256(origem)

    with patch(
        "promptvideo.core.fast_path.verificar_copia_direta",
        return_value=(True, "Compativel")
    ):
        sucesso, _ = tentar_copia_direta(
            origem, destino
        )

    assert sucesso
    assert sha256(origem) == assinatura
    assert sha256(destino) == assinatura


def test_copia_incompativel_preserva_destino(tmp_path):

    origem = tmp_path / "origem.mp4"
    destino = tmp_path / "destino.mp4"

    origem.write_bytes(b"origem")
    destino.write_bytes(b"destino anterior")

    with patch(
        "promptvideo.core.fast_path.verificar_copia_direta",
        return_value=(False, "Incompativel")
    ):
        sucesso, _ = tentar_copia_direta(
            origem, destino
        )

    assert not sucesso
    assert destino.read_bytes() == b"destino anterior"


def test_copia_mesmo_arquivo(tmp_path):

    origem = tmp_path / "origem.mp4"
    origem.write_bytes(b"original")

    sucesso, _ = tentar_copia_direta(
        origem, origem
    )

    assert not sucesso
    assert origem.read_bytes() == b"original"


def test_falha_copia_preserva_destino(tmp_path):

    origem = tmp_path / "origem.mp4"
    destino = tmp_path / "destino.mp4"

    origem.write_bytes(b"origem")
    destino.write_bytes(b"destino anterior")

    with patch(
        "promptvideo.core.fast_path.verificar_copia_direta",
        return_value=(True, "Compativel")
    ), patch(
        "shutil.copy2",
        side_effect=OSError("Falha simulada")
    ):
        sucesso, _ = tentar_copia_direta(
            origem, destino
        )

    assert not sucesso
    assert destino.read_bytes() == b"destino anterior"
    assert not list(tmp_path.glob(".fast_path_*"))


def test_falha_substituicao_preserva_destino(tmp_path):

    origem = tmp_path / "origem.mp4"
    destino = tmp_path / "destino.mp4"

    origem.write_bytes(b"origem")
    destino.write_bytes(b"destino anterior")

    with patch(
        "promptvideo.core.fast_path.verificar_copia_direta",
        return_value=(True, "Compativel")
    ), patch(
        "os.replace",
        side_effect=OSError("Falha simulada")
    ):
        sucesso, _ = tentar_copia_direta(
            origem, destino
        )

    assert not sucesso
    assert destino.read_bytes() == b"destino anterior"
    assert not list(tmp_path.glob(".fast_path_*"))


@pytest.fixture
def cache_isolado(monkeypatch):

    monkeypatch.setattr(audio, "_whisper", None)
    monkeypatch.setattr(audio, "_whisper_nome", None)


def modelo_simulado():

    palavra = SimpleNamespace(
        start=0.0,
        end=0.5,
        word="Teste"
    )

    segmento = SimpleNamespace(
        start=0.0,
        end=1.0,
        text="Teste",
        words=[palavra]
    )

    modelo = Mock()

    modelo.transcribe.side_effect = (
        lambda *a, **k: (iter([segmento]), None)
    )

    return modelo


@pytest.mark.parametrize(
    "liberar,cargas",
    [(True, 2), (False, 1)]
)
def test_cache_adaptativo(
    cache_isolado, liberar, cargas
):

    with patch(
        "promptvideo.core.whisper_manager.carregar_modelo_whisper",
        side_effect=lambda *a: modelo_simulado()
    ) as carregar, patch(
        "promptvideo.core.memory_manager.deve_liberar_whisper",
        return_value=(liberar, "Teste")
    ):

        primeiro = audio.transcrever("teste.mp4")
        segundo = audio.transcrever("teste.mp4")

        assert primeiro == segundo
        assert carregar.call_count == cargas

        assert (audio._whisper is None) == liberar


def test_cache_liberado_apos_excecao(cache_isolado):

    modelo = modelo_simulado()

    def falhar():
        raise RuntimeError("Falha simulada")
        yield

    modelo.transcribe.side_effect = (
        lambda *a, **k: (falhar(), None)
    )

    with patch(
        "promptvideo.core.whisper_manager.carregar_modelo_whisper",
        return_value=modelo
    ), patch(
        "promptvideo.core.memory_manager.deve_liberar_whisper",
        return_value=(True, "Pouca RAM")
    ):

        with pytest.raises(
            RuntimeError,
            match="Falha simulada"
        ):
            audio.transcrever("teste.mp4")

        assert audio._whisper is None
        assert audio._whisper_nome is None

        assert audio._lock_whisper.acquire(
            blocking=False
        )

        audio._lock_whisper.release()
