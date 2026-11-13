import tempfile
import unittest
from pathlib import Path
from promptvideo.features.background_music import TRACKS, escolher_musica, validar_volume

class MusicTests(unittest.TestCase):
    def test_tracks_are_shipped(self):
        for track in TRACKS[1:-1]:
            self.assertTrue(escolher_musica(track).is_file())
    def test_none(self):
        self.assertIsNone(escolher_musica())
    def test_import(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'track.mp3';p.write_bytes(b'demo')
            self.assertEqual(escolher_musica('Arquivo próprio',p),p)
    def test_missing_import(self):
        with self.assertRaises(ValueError):escolher_musica('Arquivo próprio')
    def test_bad_format(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'file.exe';p.write_bytes(b'demo')
            with self.assertRaises(ValueError):escolher_musica('Arquivo próprio',p)
    def test_volume(self):
        self.assertEqual(validar_volume(20),20)
        for v in (-1,101,float('nan')):
            with self.assertRaises(ValueError):validar_volume(v)
if __name__=='__main__':unittest.main()
