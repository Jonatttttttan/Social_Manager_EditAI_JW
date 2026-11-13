import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from promptvideo.core.batch import validar_lote, executar_lote

class TestBatch(unittest.TestCase):
    def test_validacao(self):
        with self.assertRaises(ValueError): validar_lote([], 'edite', 'Tradicional')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.mp4';p.write_bytes(b'fake')
            self.assertEqual(validar_lote([str(p)],'melhore o audio','Tradicional'),[p])
            with self.assertRaises(ValueError): validar_lote([str(p)],'','Tradicional')
            with self.assertRaises(ValueError): validar_lote([str(p)]*21,'edite','Tradicional')
    def test_falha_isolada(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.mp4'; b=Path(d)/'b.mp4'
            a.write_bytes(b'a'); b.write_bytes(b'b')
            out=Path(d)/'saida.mp4';out.write_bytes(b'ok')
            with patch('promptvideo.core.batch.preparar_video',side_effect=[RuntimeError('falhou'),('video_0002',{'cortes':[]})]), patch('promptvideo.core.batch.aplicar_proposta',return_value=str(out)), patch('promptvideo.core.batch.SAIDAS',Path(d)):
                pacote,reg=executar_lote([str(a),str(b)],'melhore o audio')
            self.assertEqual([r['status'] for r in reg],['erro','concluido'])
            self.assertTrue(Path(pacote).is_file())
if __name__=='__main__':unittest.main()
