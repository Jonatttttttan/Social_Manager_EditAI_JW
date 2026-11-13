import unittest
from promptvideo.core.transitions import validar_transicao, TRANSICOES

class TestTransitions(unittest.TestCase):
    def test_effects(self):
        self.assertEqual(TRANSICOES['Dissolver'], 'fade')
        self.assertEqual(TRANSICOES['Deslizar'], 'slideleft')
    def test_valid_duration(self):
        self.assertEqual(validar_transicao('Fade para preto', 0.7), 0.7)
    def test_reject_invalid(self):
        for name, duration in [('Desconhecida', 0.7), ('Dissolver', 0), ('Dissolver', 3), ('Dissolver', float('nan'))]:
            with self.assertRaises(ValueError): validar_transicao(name, duration)
