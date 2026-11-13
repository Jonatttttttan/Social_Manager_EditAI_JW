import unittest
from promptvideo.core.duration import planejar_duracao
from promptvideo.ai.prompts import interpretar_regras

class TestDuration(unittest.TestCase):
    def test_intencao(self):
        p=interpretar_regras('Meu vídeo tem 20 minutos. Deixe o vídeo com 8 minutos')
        self.assertEqual(p['duracao_alvo'],480)
    def test_sem_confundir_origem(self):
        p=interpretar_regras('Deixe o vídeo com 2 minutos e melhore o áudio')
        self.assertEqual(p['duracao_alvo'],120)
    def test_so_silencios(self):
        cuts,meta=planejar_duracao(100,85,[],[(10,20),(40,50)])
        self.assertAlmostEqual(meta['estimada'],85)
        self.assertTrue(meta['atingida'])
        self.assertEqual(len(cuts),2)
    def test_insuficiente(self):
        cuts,meta=planejar_duracao(100,30,[],[(10,15)])
        self.assertFalse(meta['atingida'])
        self.assertAlmostEqual(meta['estimada'],95)
        self.assertTrue(meta['limitacao'])
    def test_preserva_cortes(self):
        cuts,meta=planejar_duracao(100,85,[(0,10)],[(0,10),(20,30)])
        self.assertAlmostEqual(meta['estimada'],85)
        self.assertEqual(len(cuts),2)
    def test_nao_alonga(self):
        cuts,meta=planejar_duracao(50,100,[],[(10,20)])
        self.assertEqual(cuts,[])
        self.assertAlmostEqual(meta['estimada'],50)

if __name__=='__main__':unittest.main()
