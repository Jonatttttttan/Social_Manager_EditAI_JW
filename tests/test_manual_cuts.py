import unittest
from promptvideo.core.manual_cuts import tempo_em_segundos, interpretar_cortes_manuais, combinar_cortes

class TestManualCuts(unittest.TestCase):
    def test_tempos(self):
        self.assertEqual(tempo_em_segundos('02:30'),150)
        self.assertEqual(tempo_em_segundos('01:02:03'),3723)
    def test_varios(self):
        self.assertEqual(len(interpretar_cortes_manuais('02:30 - 03:15\n05:10 - 05:25',600)),2)
    def test_vazio(self):
        self.assertEqual(interpretar_cortes_manuais('',60),[])
    def test_fora(self):
        with self.assertRaises(ValueError): interpretar_cortes_manuais('02:30 - 03:15',100)
    def test_invertido(self):
        with self.assertRaises(ValueError): interpretar_cortes_manuais('02:30 - 02:20',600)
    def test_invalidos(self):
        for item in ('abc', '02:80 - 03:00', '01:00 - 01:00'):
            with self.subTest(item=item), self.assertRaises(ValueError): interpretar_cortes_manuais(item,600)
    def test_sobrepostos(self):
        result=combinar_cortes([{'inicio':100,'fim':130}], [{'inicio':120,'fim':150}])
        self.assertEqual(result,[{'inicio':100.0,'fim':150.0}])
