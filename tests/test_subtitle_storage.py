import json
import unittest
import tempfile

from pathlib import Path
from copy import deepcopy
from unittest.mock import patch

from promptvideo.features.subtitle_storage import (
    salvar_transcricao_original,
    carregar_transcricao,
    salvar_transcricao_corrigida,
)


class TestSubtitleStorage(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.pasta = Path(self.temp.name)
        self.original = self.pasta / "original.json"
        self.corrigida = self.pasta / "corrigida.json"

        self.segmentos = [
            {
                "inicio": 0.0,
                "fim": 3.0,
                "texto": "Eu utilizo Paiton",
                "palavras": [
                    {"inicio": 0.0, "fim": 0.5, "texto": "Eu"},
                    {"inicio": 0.5, "fim": 1.5, "texto": "utilizo"},
                    {"inicio": 1.5, "fim": 3.0, "texto": "Paiton"},
                ],
            }
        ]

    def salvar_original(self):
        return salvar_transcricao_original(
            self.original,
            self.segmentos,
            "Tradicional",
            "Cl\u00e1ssica",
            100,
            "Inferior"
        )

    def test_01_salvar_original(self):
        self.salvar_original()
        self.assertTrue(self.original.is_file())

    def test_02_recuperar_segmentos(self):
        self.salvar_original()
        dados = carregar_transcricao(self.original)

        self.assertEqual(dados["segmentos"], self.segmentos)
        self.assertEqual(dados["tipo"], "original")
        self.assertEqual(dados["versao_formato"], 1)

    def test_03_preservar_configuracoes(self):
        self.salvar_original()
        dados = carregar_transcricao(self.original)

        self.assertEqual(
            dados["configuracoes"],
            {'estilo': 'Tradicional', 'visual': 'Clássica', 'tamanho': 100, 'posicao': 'Inferior', 'transicoes': {'abertura': 'Nenhuma', 'duracao_abertura': 1.0, 'encerramento': 'Nenhuma', 'duracao_encerramento': 1.0}}
        )

    def test_04_impedir_sobrescrita_original(self):
        self.salvar_original()
        antes = self.original.read_bytes()

        with self.assertRaises(FileExistsError):
            self.salvar_original()

        self.assertEqual(self.original.read_bytes(), antes)

    def test_05_salvar_correcao(self):
        self.salvar_original()

        salvar_transcricao_corrigida(
            self.original,
            self.corrigida,
            ["Eu utilizo Python"]
        )

        dados = carregar_transcricao(self.corrigida)

        self.assertEqual(dados["tipo"], "corrigida")
        self.assertEqual(
            dados["segmentos"][0]["texto"],
            "Eu utilizo Python"
        )

    def test_06_preservar_original_apos_correcao(self):
        self.salvar_original()
        antes = self.original.read_bytes()

        salvar_transcricao_corrigida(
            self.original,
            self.corrigida,
            ["Eu utilizo Python"]
        )

        self.assertEqual(self.original.read_bytes(), antes)

    def test_07_atualizar_correcao(self):
        self.salvar_original()

        for texto in ("Eu utilizo Python", "Eu estudo Python"):
            salvar_transcricao_corrigida(
                self.original,
                self.corrigida,
                [texto]
            )

        dados = carregar_transcricao(self.corrigida)

        self.assertEqual(
            dados["segmentos"][0]["texto"],
            "Eu estudo Python"
        )

    def test_08_bloquear_mesmo_destino(self):
        self.salvar_original()

        with self.assertRaises(ValueError):
            salvar_transcricao_corrigida(
                self.original,
                self.original,
                ["Eu utilizo Python"]
            )

    def test_09_rejeitar_arquivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            carregar_transcricao(self.original)

    def test_10_rejeitar_json_corrompido(self):
        self.original.write_text(
            "{json invalido",
            encoding="utf-8"
        )

        with self.assertRaises(json.JSONDecodeError):
            carregar_transcricao(self.original)

    def test_11_rejeitar_versao_incompativel(self):
        self.salvar_original()

        dados = carregar_transcricao(self.original)
        dados["versao_formato"] = 999

        self.original.write_text(
            json.dumps(dados),
            encoding="utf-8"
        )

        with self.assertRaises(ValueError):
            carregar_transcricao(self.original)

    def test_12_preservar_correcao_em_caso_de_falha(self):
        self.salvar_original()

        salvar_transcricao_corrigida(
            self.original,
            self.corrigida,
            ["Eu utilizo Python"]
        )

        antes = self.corrigida.read_bytes()

        with patch(
            "promptvideo.features.subtitle_storage.os.replace",
            side_effect=OSError("Falha simulada")
        ):
            with self.assertRaises(OSError):
                salvar_transcricao_corrigida(
                    self.original,
                    self.corrigida,
                    ["Eu estudo Python"]
                )

        self.assertEqual(self.corrigida.read_bytes(), antes)

        temporarios = list(self.pasta.glob(".legendas_*.tmp"))
        self.assertEqual(temporarios, [])


if __name__ == "__main__":
    unittest.main()
