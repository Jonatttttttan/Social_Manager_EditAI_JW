import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from promptvideo import licensing

class LicenseClientTests(unittest.TestCase):
    def test_activation_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(licensing, 'data_dir', return_value=Path(tmp)), patch.object(licensing, 'server_url', return_value='http://127.0.0.1:5000'):
            def fake_post(endpoint, payload):
                if endpoint.endswith('activate'):
                    self.assertEqual(payload['key'], 'TEST-KEY')
                    return {'activation_token': 'token-test'}
                self.assertEqual(payload['activation_token'], 'token-test')
                return {'valid': True, 'revoked': False, 'expires_at': '2099-01-01T00:00:00+00:00'}
            with patch.object(licensing, '_post', side_effect=fake_post):
                self.assertTrue(licensing.activate('TEST-KEY')['valid'])
                self.assertTrue(licensing.validate()['valid'])
    def test_revoked_license_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(licensing, 'data_dir', return_value=Path(tmp)), patch.object(licensing, 'server_url', return_value='http://127.0.0.1:5000'):
            with patch.object(licensing, '_post', side_effect=[{'activation_token': 'token'}, {'valid': True, 'expires_at': '2099-01-01T00:00:00+00:00'}, {'valid': False, 'revoked': True}]):
                licensing.activate('KEY')
                with self.assertRaises(licensing.LicenseError):
                    licensing.validate()

    def test_offline_grace_and_expiry(self):
        import urllib.error
        with tempfile.TemporaryDirectory() as tmp, patch.object(licensing, 'data_dir', return_value=Path(tmp)), patch.object(licensing, 'server_url', return_value='https://example.test'):
            with patch.object(licensing, '_post', side_effect=[{'activation_token': 'tok'}, {'valid': True, 'revoked': False, 'expires_at': '2099-01-01T00:00:00+00:00'}]):
                licensing.activate('KEY')
            now = licensing.time.time()
            with patch.object(licensing, '_post', side_effect=licensing.LicenseError('offline')) as mocked:
                mocked.side_effect.__cause__ = urllib.error.URLError('offline')
                with patch.object(licensing.time, 'time', return_value=now + 3600):
                    self.assertTrue(licensing.validate()['offline'])
                with patch.object(licensing.time, 'time', return_value=now + 86401):
                    with self.assertRaises(licensing.LicenseError):
                        licensing.validate()

    def test_http_denial_never_uses_offline_grace(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(licensing, 'data_dir', return_value=Path(tmp)), patch.object(licensing, 'server_url', return_value='https://example.test'):
            with patch.object(licensing, '_post', side_effect=[{'activation_token': 'tok'}, {'valid': True, 'revoked': False, 'expires_at': '2099-01-01T00:00:00+00:00'}]):
                licensing.activate('KEY')
            with patch.object(licensing, '_post', side_effect=licensing.LicenseError('invalid_activation')):
                with self.assertRaises(licensing.LicenseError):
                    licensing.validate()

if __name__ == '__main__':
    unittest.main()
