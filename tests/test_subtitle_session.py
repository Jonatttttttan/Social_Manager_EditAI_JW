import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

from promptvideo.features import subtitle_session as sessao


class TestSubtitleSession(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.raiz = Path(self.temp.name)

        self.patcher = patch.object(
            sessao, "BASE", self.raiz
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.video = self.raiz / "entrada.mp4"
        self.video.write_bytes(b"video-base-simulado")

        self.segmentos = [
            {
                "inicio": 0.0,
                "fim": 3.0,
                "texto": "Eu utilizo Paiton",
                "palavras": [
                    {"inicio": 0.0, "fim": 0.5, "texto": "Eu"},
                    {"inicio": 0.5, "fim": 1.5, "texto": "utilizo"},
                    {"inicio": 1.5, "fim": 3.0, "texto": "Paiton"}
                ]
            }
        ]

    def criar(self):
        return sessao.criar_sessao_revisao(
            self.video,
            self.segmentos,
            "Tradicional",
            "Cl\u00e1ssica",
            100,
            "Inferior"
        )

    def test_01_criar_sessao(self):
        identificador = self.criar()

        self.assertRegex(
            identificador, r"^[a-f0-9]{32}$"
        )

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        self.assertTrue(
            Path(dados["video_base"]).is_file()
        )

        self.assertTrue(
            Path(dados["arquivo_original"]).is_file()
        )

    def test_02_preservar_video_independente(self):
        identificador = self.criar()
        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        copia = Path(dados["video_base"])
        antes = copia.read_bytes()

        self.video.write_bytes(b"video-modificado")

        self.assertEqual(copia.read_bytes(), antes)

    def test_03_isolar_sessoes(self):
        primeiro = self.criar()
        segundo = self.criar()

        self.assertNotEqual(primeiro, segundo)

        sessao.salvar_revisao(
            primeiro, ["Eu utilizo Python"]
        )

        dados = sessao.carregar_sessao_revisao(
            segundo
        )

        self.assertIsNone(dados["corrigida"])

    def test_04_recuperar_transcricao(self):
        identificador = self.criar()

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        self.assertEqual(
            dados["original"]["segmentos"],
            self.segmentos
        )

    def test_05_salvar_revisao(self):
        identificador = self.criar()

        sessao.salvar_revisao(
            identificador,
            ["Eu utilizo Python"]
        )

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        self.assertEqual(
            dados["corrigida"]["segmentos"][0]["texto"],
            "Eu utilizo Python"
        )

        self.assertEqual(
            dados["original"]["segmentos"],
            self.segmentos
        )

    def test_06_restaurar_revisao(self):
        identificador = self.criar()

        sessao.salvar_revisao(
            identificador,
            ["Eu utilizo Python"]
        )

        restaurados = sessao.restaurar_revisao(
            identificador
        )

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        self.assertEqual(restaurados, self.segmentos)
        self.assertIsNone(dados["corrigida"])

    def test_07_detectar_video_alterado(self):
        identificador = self.criar()

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        Path(dados["video_base"]).write_bytes(
            b"arquivo-alterado"
        )

        with self.assertRaises(RuntimeError):
            sessao.carregar_sessao_revisao(
                identificador
            )

    def test_08_rejeitar_identificadores_invalidos(self):
        for identificador in (
            "../",
            "../../arquivo",
            "",
            None,
            "sessao-invalida"
        ):
            with self.subTest(identificador=identificador):
                with self.assertRaises(ValueError):
                    sessao.carregar_sessao_revisao(
                        identificador
                    )

    def test_09_rejeitar_sessao_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            sessao.carregar_sessao_revisao("a" * 32)

    def test_10_rejeitar_video_inexistente(self):
        self.video.unlink()

        with self.assertRaises(FileNotFoundError):
            self.criar()

    def test_11_rejeitar_video_vazio(self):
        self.video.write_bytes(b"")

        with self.assertRaises(ValueError):
            self.criar()

    def test_12_exportar_legendas_originais(self):
        identificador = self.criar()

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        with patch.object(
            sessao,
            "renderizar_legendas_salvas",
            return_value=("saida.mp4", "saida.srt")
        ) as renderizador:

            resultado = sessao.exportar_revisao(
                identificador
            )

            renderizador.assert_called_once_with(
                dados["video_base"],
                dados["arquivo_original"],
                callback=None
            )

            self.assertEqual(
                resultado,
                ("saida.mp4", "saida.srt")
            )

    def test_13_exportar_legendas_corrigidas(self):
        identificador = self.criar()

        sessao.salvar_revisao(
            identificador,
            ["Eu utilizo Python"]
        )

        dados = sessao.carregar_sessao_revisao(
            identificador
        )

        with patch.object(
            sessao,
            "renderizar_legendas_salvas",
            return_value=("corrigido.mp4", "corrigido.srt")
        ) as renderizador:

            sessao.exportar_revisao(identificador)

            renderizador.assert_called_once_with(
                dados["video_base"],
                dados["arquivo_corrigido"],
                callback=None
            )

    def test_14_limpar_sessao_apos_falha(self):
        with patch.object(
            sessao,
            "salvar_transcricao_original",
            side_effect=OSError("Falha simulada")
        ):
            with self.assertRaises(OSError):
                self.criar()

        raiz = self.raiz / "revisoes_legendas"

        self.assertEqual(list(raiz.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
