import unittest
from unittest.mock import patch
from promptvideo.diagnostics import diagnosticar
from promptvideo.core.media import juntar_intervalos, trechos_preservados

class TestIntegridade(unittest.TestCase):
    def test_intervalos_unidos(self):
        self.assertEqual(juntar_intervalos([(2, 3), (2.5, 4)], 10), [(2.0, 4.0)])

    def test_trechos_preservados(self):
        self.assertEqual(trechos_preservados([(2, 4)], 6), [(0.0, 2.0), (4.0, 6)])

    @patch('promptvideo.diagnostics.subprocess.run')
    def test_diagnostico(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = 'ffmpeg version teste\n'
        dados = diagnosticar()
        self.assertIn('ferramentas', dados)
        self.assertTrue(dados['ferramentas']['ffmpeg']['encontrado'])
