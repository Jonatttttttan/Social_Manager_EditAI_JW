import unittest
from promptvideo.ai.prompts import interpretar_regras

class TestLinguagemNatural(unittest.TestCase):
    def test_sinonimos(self):
        for frase in ('Tira as pausas grandes', 'Corte os momentos em que não estou falando',
                      'Elimine os silêncios desnecessários', 'Encurte as pausas'):
            with self.subTest(frase=frase):
                self.assertTrue(interpretar_regras(frase)['silencios'])

    def test_combinacao(self):
        p = interpretar_regras('Tira as pausas maiores que 2,5 segundos e limpa o chiado')
        self.assertTrue(p['silencios'])
        self.assertEqual(p['minimo'], 2.5)
        self.assertEqual(p['ruido'], 'medio')

    def test_audio(self):
        self.assertTrue(interpretar_regras('Deixa minha voz mais clara')['melhorar_audio'])
        self.assertTrue(interpretar_regras('Aumente o volume')['melhorar_audio'])

    def test_frase(self):
        p = interpretar_regras('Apaga quando eu disser "vou recomeçar"')
        self.assertEqual(p['frases'], ['vou recomeçar'])

    def test_negacao(self):
        p = interpretar_regras('Não remova os silêncios, apenas melhore o áudio')
        self.assertFalse(p['silencios'])
        self.assertTrue(p['melhorar_audio'])

    def test_sem_acao(self):
        with self.assertRaises(ValueError):
            interpretar_regras('Faça um vídeo viral com legendas animadas')

if __name__ == '__main__':
    unittest.main()
