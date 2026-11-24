"""Cliente OAuth Instagram: não lê nem armazena o token da Meta."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from promptvideo import licensing
from promptvideo.config import INSTAGRAM_ENABLED

class InstagramOAuthClientError(RuntimeError):
    pass

def _config():
    # Testes locais: token de ativação local SOMENTE por variável de ambiente.
    # Não modificar o license.json de produção.
    base = os.environ.get('EDITAI_INSTAGRAM_SERVER', 'http://127.0.0.1:5000').rstrip('/')
    if not (base.startswith('http://127.0.0.1:') or base.startswith('http://localhost:') or base.startswith('https://')):
        raise InstagramOAuthClientError('Endereço do servidor Instagram inválido.')
    activation = os.environ.get('EDITAI_INSTAGRAM_ACTIVATION', '').strip()
    if not activation:
        # Usa a licença normal apenas se a URL do servidor for a mesma.
        try:
            state = licensing._load()
            if state.get('server_url', '').rstrip('/') == base:
                activation = state.get('activation_token', '')
        except (OSError, ValueError):
            pass
    if not activation:
        raise InstagramOAuthClientError('Defina EDITAI_INSTAGRAM_ACTIVATION com o token de ativação do servidor LOCAL (não use o token de produção).')
    return base, {'X-EditAI-Activation': activation, 'X-EditAI-Device': licensing.device_id()}

def _call(method, path):
    _garantir_instagram_habilitado()
    base, headers = _config()
    req = Request(base + path, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except HTTPError as exc:
        raise InstagramOAuthClientError(f'Servidor recusou a operação (HTTP {exc.code}).') from None
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise InstagramOAuthClientError('Não foi possível consultar o servidor Instagram local.') from exc
    if not isinstance(data, dict):
        raise InstagramOAuthClientError('Resposta inválida do servidor Instagram.')
    return data

def conectar_instagram():
    _garantir_instagram_habilitado()
    data = _call('POST', '/api/instagram/connect')
    url = data.get('authorization_url', '')
    if not isinstance(url, str) or not url.startswith('https://'):
        raise InstagramOAuthClientError('O servidor não retornou uma URL segura de autorização.')
    return url

def status_instagram():
    _garantir_instagram_habilitado()
    return _call('GET', '/api/instagram/status')

def desconectar_instagram():
    _garantir_instagram_habilitado()
    return _call('POST', '/api/instagram/disconnect')


def _reels_request(method, path, payload=None, content_type=None, timeout=90):
    _garantir_instagram_habilitado()
    base, headers = _config()
    if content_type:
        headers['Content-Type'] = content_type
    req = Request(base + path, data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as exc:
        raise InstagramOAuthClientError(f'Operação de Reel recusada pelo servidor (HTTP {exc.code}).') from None
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise InstagramOAuthClientError('Falha de comunicação com o servidor de Reels.') from exc

def preparar_reel_servidor(video_path, caption):
    _garantir_instagram_habilitado()
    import uuid
    import mimetypes
    path = Path(video_path)
    if not path.is_file() or path.suffix.lower() != '.mp4':
        raise InstagramOAuthClientError('Exporte um vídeo MP4 válido antes de publicar.')
    if path.stat().st_size > 250 * 1024 * 1024:
        raise InstagramOAuthClientError('O vídeo ultrapassa o limite de 250 MB desta versão de testes.')
    boundary = '----EditAI' + uuid.uuid4().hex
    # Versao local de testes: arquivo inteiro em memoria, limitado a 250 MB.
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="video.mp4"\r\n'
            'Content-Type: video/mp4\r\n\r\n').encode('utf-8') + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
    return _reels_request('POST', '/api/instagram/reels/prepare', body, f'multipart/form-data; boundary={boundary}', 180)

def criar_container_reel(job_id):
    _garantir_instagram_habilitado()
    return _reels_request('POST', f'/api/instagram/reels/{job_id}/create', b'', 'application/json')

def consultar_reel(job_id):
    _garantir_instagram_habilitado()
    return _reels_request('GET', f'/api/instagram/reels/{job_id}/status')

def publicar_reel_servidor(job_id):
    _garantir_instagram_habilitado()
    return _reels_request('POST', f'/api/instagram/reels/{job_id}/publish', b'{"confirm":true}', 'application/json')

def _garantir_instagram_habilitado():
    if not INSTAGRAM_ENABLED:
        raise InstagramOAuthClientError(
            "A integra\u00e7\u00e3o com o Instagram est\u00e1 desativada nesta vers\u00e3o do EditAI."
        )
