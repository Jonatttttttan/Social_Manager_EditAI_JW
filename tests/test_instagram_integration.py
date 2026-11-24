from pathlib import Path
from unittest.mock import patch, Mock
import pytest
from promptvideo.integrations.instagram import preparar_reel, publicar_reel, InstagramPublishError



@pytest.fixture(autouse=True)
def habilitar_instagram_em_teste(monkeypatch):
    monkeypatch.setattr(
        "promptvideo.integrations.instagram.INSTAGRAM_ENABLED",
        True
    )

def test_preparar_sem_token(tmp_path):
    video = tmp_path / 'video.mp4'
    video.write_bytes(b'mp4')
    with pytest.raises(InstagramPublishError, match='token'):
        preparar_reel(video, '17841459163376040', '')

def test_preparar_upload_sem_publicar(tmp_path):
    video = tmp_path / 'video.mp4'
    video.write_bytes(b'fake-video')
    create = Mock(ok=True)
    create.json.return_value = {'id':'container123','uri':'https://rupload.facebook.com/ig-api-upload/123'}
    upload = Mock()
    upload.raise_for_status.return_value = None
    with patch('promptvideo.integrations.instagram.requests.request', return_value=create) as req, \
         patch('promptvideo.integrations.instagram.requests.post', return_value=upload) as post:
        assert preparar_reel(video, '17841459163376040', 'token', 'legenda') == 'container123'
        assert req.call_args.args[1].endswith('/media')
        assert post.call_count == 1

def test_publicacao_exige_video_finalizado():
    status = Mock(ok=True)
    status.json.return_value = {'status_code':'IN_PROGRESS'}
    with patch('promptvideo.integrations.instagram.requests.request', return_value=status) as req:
        with pytest.raises(InstagramPublishError, match='não está pronto'):
            publicar_reel('17841459163376040','container123','token')
        assert req.call_count == 1

def test_publicacao_quando_finalizado():
    status = Mock(ok=True)
    status.json.return_value = {'status_code':'FINISHED'}
    published = Mock(ok=True)
    published.json.return_value = {'id':'reel456'}
    with patch('promptvideo.integrations.instagram.requests.request', side_effect=[status,published]) as req:
        assert publicar_reel('17841459163376040','container123','token') == 'reel456'
        assert req.call_args.args[1].endswith('/media_publish')
