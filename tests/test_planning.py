import unittest
from promptvideo.ai.prompts import interpretar_regras
from promptvideo.core.media import trechos_preservados
class TestPlan(unittest.TestCase):
    def test_prompt(self):
        p=interpretar_regras('Remova os silêncios maiores que 1 segundo e reduza o ruído de fundo')
        self.assertTrue(p['silencios'])
        self.assertEqual(p['ruido'],'medio')
    def test_intervals(self):
        self.assertEqual(trechos_preservados([(2,4)],6),[(0.,2.),(4.,6)])
if __name__ == '__main__':unittest.main()
