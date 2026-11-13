import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from promptvideo.core.batch import executar_lote

class TestBatchTransitions(unittest.TestCase):
    def test_transicoes_propagadas_e_registradas(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            videos = [base / 'primeiro.mp4', base / 'segundo.mov']
            for video in videos: video.write_bytes(b'teste')
            resultado = base / 'editado.mp4'
            resultado.write_bytes(b'video')
            with patch('promptvideo.core.batch.SAIDAS', base), \
                 patch('promptvideo.core.batch.preparar_video', side_effect=[('video_0001', {'cortes': []}), ('video_0002', {'cortes': []})]), \
                 patch('promptvideo.core.batch.aplicar_proposta', return_value=str(resultado)) as aplicar:
                pacote, registros = executar_lote([str(v) for v in videos], 'remova pausas', transicao='Dissolver', duracao_transicao=0.7)
            self.assertEqual(len(registros), 2)
            self.assertTrue(all(r['status'] == 'concluido' for r in registros))
            self.assertEqual(aplicar.call_count, 2)
            for call in aplicar.call_args_list:
                self.assertEqual(call.kwargs['transicao'], 'Dissolver')
                self.assertEqual(call.kwargs['duracao_transicao'], 0.7)
            with zipfile.ZipFile(pacote) as arquivo:
                relatorio = json.loads(arquivo.read('relatorio.json'))
            self.assertEqual(relatorio['transicao'], 'Dissolver')
            self.assertEqual(relatorio['duracao_transicao'], 0.7)

    def test_efeito_invalido_bloqueado_antes_de_processar(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / 'a.mp4'
            video.write_bytes(b'teste')
            with self.assertRaises(ValueError):
                executar_lote([str(video)], 'edite', transicao='invalido')

if __name__ == '__main__': unittest.main()
