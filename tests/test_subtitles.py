import unittest
from promptvideo.features.subtitles import _srt_time, _chunks, _ass

class TestSubtitles(unittest.TestCase):
    def test_srt_time(self):
        self.assertEqual(_srt_time(61.25),'00:01:01,250')
    def test_chunks(self):
        s=[{'inicio':0,'fim':2,'texto':'Olá mundo','palavras':[{'inicio':0,'fim':.4,'texto':'Olá'},{'inicio':.5,'fim':1,'texto':'mundo'}]}]
        self.assertEqual(_chunks(s),[(0.0,1.0,'Olá mundo')])
    def test_ass_traditional(self):
        self.assertIn('Olá mundo',_ass([{'inicio':0,'fim':1,'texto':'Olá mundo','palavras':[]}],'Tradicional',1280,720))
    def test_ass_dynamic(self):
        self.assertIn('Dialogue:',_ass([{'inicio':0,'fim':1,'texto':'Oi','palavras':[{'inicio':0,'fim':1,'texto':'Oi'}]}],'Dinâmica',1280,720))

if __name__=='__main__': unittest.main()
