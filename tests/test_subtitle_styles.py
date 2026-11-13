import unittest
from promptvideo.features.subtitles import ESTILOS_VISUAIS, _ass, validar_aparencia

class TestSubtitleStyles(unittest.TestCase):
    def test_six_styles(self):
        self.assertEqual(len(ESTILOS_VISUAIS), 6)
        for visual in ESTILOS_VISUAIS:
            self.assertIn('Style: Tradicional', _ass([{'inicio':0,'fim':1,'texto':'Teste','palavras':[]}], 'Tradicional',1280,720,visual))
    def test_position(self):
        for pos in ('Inferior','Centro','Superior'):
            self.assertIn('Dialogue:',_ass([{'inicio':0,'fim':1,'texto':'Teste','palavras':[]}],'Tradicional',1280,720,'Neon',120,pos))
    def test_invalid(self):
        with self.assertRaises(ValueError): validar_aparencia('inexistente')
        with self.assertRaises(ValueError): validar_aparencia('Clássica',999)
        with self.assertRaises(ValueError): validar_aparencia('Clássica',100,'Lateral')
