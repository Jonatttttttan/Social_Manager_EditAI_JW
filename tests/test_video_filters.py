import unittest
from promptvideo.features.video_filters import FILTROS, validar_filtros, montar_filtro

class TestVideoFilters(unittest.TestCase):
    def test_presets(self):
        for filtro in FILTROS:
            self.assertEqual(validar_filtros(filtro,60,0,0),(60.0,0.0,0.0))
    def test_original_noop(self):
        self.assertIsNone(montar_filtro('Original'))
    def test_zero_intensity(self):
        self.assertIsNone(montar_filtro('Vintage',0))
    def test_manual_adjustments(self):
        self.assertIn('eq=',montar_filtro('Original',60,20,-10))
    def test_reject_injection(self):
        with self.assertRaises(ValueError): montar_filtro('eq=evil',60,0,0)
    def test_reject_nan(self):
        with self.assertRaises(ValueError): montar_filtro('Vibrante',float('nan'),0,0)
    def test_reject_out_of_range(self):
        with self.assertRaises(ValueError): montar_filtro('Suave',60,101,0)
