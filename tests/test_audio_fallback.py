import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from promptvideo.features import audio_enhancer as ae

class TestAudioFallback(unittest.TestCase):
    def test_loudnorm_invalid_falls_back_to_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'entrada.mp4'
            target = Path(tmp) / 'saida.mp4'
            original.write_bytes(b'arquivo simulado')
            with patch.object(ae, 'analisar_video', return_value={'possui_audio': True}), patch.object(ae, '_medir_loudnorm', return_value=None):
                result = ae.melhorar_audio(original, target)
            self.assertEqual(result, target)
            self.assertEqual(target.read_bytes(), original.read_bytes())

    def test_loudnorm_negative_infinity_is_not_accepted(self):
        from types import SimpleNamespace
        stderr = '[Parsed_loudnorm] {"input_i":"-inf","input_tp":"-inf","input_lra":"0.00","input_thresh":"-inf","target_offset":"inf"}'
        with patch.object(ae, 'executar', return_value=SimpleNamespace(stderr=stderr)):
            self.assertIsNone(ae._medir_loudnorm('video.mp4'))
