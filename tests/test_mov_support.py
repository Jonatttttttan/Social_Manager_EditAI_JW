import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from promptvideo.core.batch import validar_lote
from promptvideo.core.jobs import salvar_video_entrada, aplicar_proposta
from promptvideo.core.media import validar_extensao_video

class TestMovSupport(unittest.TestCase):
    def test_extensoes_e_lote_misto(self):
        with tempfile.TemporaryDirectory() as d:
            mp4=Path(d)/'a.MP4'; mov=Path(d)/'b.MOV'; avi=Path(d)/'c.avi'
            for p in (mp4,mov,avi): p.write_bytes(b'conteudo')
            self.assertEqual(validar_extensao_video(mov),mov)
            self.assertEqual(validar_lote([str(mp4),str(mov)],'melhore audio','Tradicional'),[mp4,mov])
            with self.assertRaises(ValueError): validar_lote([str(avi)],'melhore audio','Tradicional')
            with self.assertRaises(ValueError): validar_extensao_video(avi)
    def test_copia_mov_preserva_extensao(self):
        with tempfile.TemporaryDirectory() as d:
            origem=Path(d)/'captura.MOV'; origem.write_bytes(b'video simulado')
            entradas=Path(d)/'entradas'; entradas.mkdir()
            with patch('promptvideo.core.jobs.ENTRADAS',entradas), patch('promptvideo.core.jobs.reservar_identificador',return_value='video_0012'), patch('promptvideo.core.media.analisar_video',return_value={'duracao':5}):
                identificador,destino=salvar_video_entrada(origem)
            self.assertEqual(identificador,'video_0012')
            self.assertEqual(destino.name,'video_0012.mov')
            self.assertEqual(destino.read_bytes(),origem.read_bytes())

if __name__=='__main__': unittest.main()
