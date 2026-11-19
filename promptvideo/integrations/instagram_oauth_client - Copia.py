"""Cliente OAuth Instagram: não lê nem armazena o token da Meta."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from promptvideo import licensing

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
    data = _call('POST', '/api/instagram/connect')
    url = data.get('authorization_url', '')
    if not isinstance(url, str) or not url.startswith('https://'):
        raise InstagramOAuthClientError('O servidor não retornou uma URL segura de autorização.')
    return url

def status_instagram():
    return _call('GET', '/api/instagram/status')

def desconectar_instagram():
    return _call('POST', '/api/instagram/disconnect')
