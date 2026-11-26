import unittest
from copy import deepcopy

from promptvideo.features.subtitle_editor import (
    corrigir_segmento,
    corrigir_segmentos,
    restaurar_segmentos,
)


class TestSubtitleEditor(unittest.TestCase):

    def setUp(self):
        self.segmento = {
            "inicio": 0.0,
            "fim": 3.0,
            "texto": "Eu utilizo Paiton",
            "palavras": [
                {"inicio": 0.0, "fim": 0.5, "texto": "Eu"},
                {"inicio": 0.5, "fim": 1.5, "texto": "utilizo"},
                {"inicio": 1.5, "fim": 3.0, "texto": "Paiton"},
            ],
        }

    def test_01_preservar_segmento_inalterado(self):
        resultado = corrigir_segmento(
            self.segmento, self.segmento["texto"]
        )
        self.assertEqual(resultado, self.segmento)
        self.assertIsNot(resultado, self.segmento)

    def test_02_nao_modificar_original(self):
        original = deepcopy(self.segmento)
        corrigir_segmento(self.segmento, "Eu utilizo Python")
        self.assertEqual(self.segmento, original)

    def test_03_independencia_das_palavras(self):
        resultado = corrigir_segmento(
            self.segmento, "Eu utilizo Python"
        )
        resultado["palavras"][0]["texto"] = "Outro"
        self.assertEqual(
            self.segmento["palavras"][0]["texto"], "Eu"
        )

    def test_04_corrigir_texto(self):
        resultado = corrigir_segmento(
            self.segmento, "Eu utilizo Python"
        )
        self.assertEqual(resultado["texto"], "Eu utilizo Python")
        self.assertEqual(
            resultado["palavras"][-1]["texto"], "Python"
        )

    def test_05_preservar_tempos_individuais(self):
        resultado = corrigir_segmento(
            self.segmento, "Eu utilizo Python"
        )
        for antes, depois in zip(
            self.segmento["palavras"], resultado["palavras"]
        ):
            self.assertEqual(antes["inicio"], depois["inicio"])
            self.assertEqual(antes["fim"], depois["fim"])

    def test_06_adicionar_palavras(self):
        resultado = corrigir_segmento(
            self.segmento, "Eu utilizo a linguagem Python"
        )
        palavras = resultado["palavras"]

        self.assertEqual(len(palavras), 5)
        self.assertAlmostEqual(palavras[0]["inicio"], 0.0)
        self.assertAlmostEqual(palavras[-1]["fim"], 3.0)

        for i, palavra in enumerate(palavras):
            self.assertAlmostEqual(palavra["inicio"], i * 0.6)
            self.assertAlmostEqual(palavra["fim"], (i + 1) * 0.6)

    def test_07_reduzir_palavras(self):
        resultado = corrigir_segmento(
            self.segmento, "Utilizo Python"
        )
        palavras = resultado["palavras"]

        self.assertEqual(len(palavras), 2)
        self.assertAlmostEqual(palavras[0]["inicio"], 0.0)
        self.assertAlmostEqual(palavras[0]["fim"], 1.5)
        self.assertAlmostEqual(palavras[1]["inicio"], 1.5)
        self.assertAlmostEqual(palavras[1]["fim"], 3.0)

    def test_08_corrigir_varios_segmentos(self):
        segmentos = [
            deepcopy(self.segmento),
            deepcopy(self.segmento),
        ]

        resultado = corrigir_segmentos(
            segmentos,
            ["Eu utilizo Python", "Aprendo Python"]
        )

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]["texto"], "Eu utilizo Python")
        self.assertEqual(resultado[1]["texto"], "Aprendo Python")

    def test_09_rejeitar_texto_vazio(self):
        for texto in ("", "   ", "\n\t"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    corrigir_segmento(self.segmento, texto)

    def test_10_rejeitar_tipo_invalido(self):
        for texto in (None, 123, [], {}):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    corrigir_segmento(self.segmento, texto)

    def test_11_rejeitar_intervalo_invertido(self):
        segmento = deepcopy(self.segmento)
        segmento["inicio"] = 5.0

        with self.assertRaises(ValueError):
            corrigir_segmento(segmento, "Python")

    def test_12_rejeitar_tempo_nao_finito(self):
        for valor in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(valor=valor):
                segmento = deepcopy(self.segmento)
                segmento["fim"] = valor

                with self.assertRaises(ValueError):
                    corrigir_segmento(segmento, "Python")

    def test_13_rejeitar_quantidade_incompativel(self):
        with self.assertRaises(ValueError):
            corrigir_segmentos([self.segmento], [])

    def test_14_rejeitar_lista_vazia(self):
        with self.assertRaises(ValueError):
            corrigir_segmentos([], [])

    def test_15_restaurar_originais(self):
        originais = [deepcopy(self.segmento)]
        corrigidos = corrigir_segmentos(
            originais, ["Eu utilizo Python"]
        )

        restaurados = restaurar_segmentos(originais)

        self.assertEqual(restaurados, originais)
        self.assertNotEqual(restaurados, corrigidos)

        restaurados[0]["palavras"][0]["texto"] = "Alterado"

        self.assertEqual(
            originais[0]["palavras"][0]["texto"], "Eu"
        )


if __name__ == "__main__":
    unittest.main()
