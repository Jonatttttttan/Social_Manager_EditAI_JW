"""Cliente de licenciamento EditAI JW. Sem segredos administrativos no cliente."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
from datetime import datetime, timezone
import urllib.error
import urllib.request

DEFAULT_SERVER = 'https://editai-license-server-jw.onrender.com'
OFFLINE_GRACE_SECONDS = 24 * 60 * 60
CLOCK_TOLERANCE_SECONDS = 120

class LicenseError(RuntimeError):
    pass

def server_url():
    return os.environ.get('EDITAI_LICENSE_SERVER', DEFAULT_SERVER).rstrip('/')

def data_dir():
    base = os.environ.get('LOCALAPPDATA') or str(Path.home() / '.local' / 'share')
    folder = Path(base) / 'EditAI Videos JW'
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def _state_path():
    return data_dir() / 'license.json'

def _load():
    try:
        return json.loads(_state_path().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}

def _save(state):
    path = _state_path()
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(state), encoding='utf-8')
    temp.replace(path)

def device_id():
    state = _load()
    if not state.get('device_id'):
        state['device_id'] = secrets.token_hex(24)
        _save(state)
    return state['device_id']

def _post(endpoint, payload):
    url = server_url() + endpoint
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read().decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            result = {}
        raise LicenseError(result.get('error') or result.get('message') or f'Servidor recusou a licença (HTTP {exc.code}).') from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LicenseError('Não foi possível acessar o servidor de licenças. Verifique se ele está ligado e o endereço configurado.') from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise LicenseError('Resposta inválida do servidor de licenças.') from exc

def activate(key):
    key = key.strip()
    if not key:
        raise LicenseError('Informe uma chave de licença.')
    result = _post('/api/licenses/activate', {'key': key, 'device_id': device_id()})
    token = result.get('activation_token')
    if not token:
        raise LicenseError('O servidor não retornou um token de ativação.')
    state = _load()
    state['activation_token'] = token
    state['server_url'] = server_url()
    state.pop('last_online_validation', None)
    state.pop('last_clock_seen', None)
    state.pop('last_expires_at', None)
    _save(state)
    return validate()

def _expiry_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (ValueError, OverflowError):
        return None


def _offline_fallback(state):
    now = time.time()
    last = state.get('last_online_validation')
    seen = state.get('last_clock_seen')
    expiry = _expiry_timestamp(state.get('last_expires_at'))
    if (type(last) not in (float, int) or type(seen) not in (float, int)
            or expiry is None):
        raise LicenseError('É necessária uma validação online antes do uso offline.')
    if now + CLOCK_TOLERANCE_SECONDS < seen or now + CLOCK_TOLERANCE_SECONDS < last:
        raise LicenseError('Relógio do computador alterado. Conecte-se para validar a licença.')
    if now >= expiry:
        raise LicenseError('Licença expirada. Conecte-se para validar a licença.')
    if now - last > OFFLINE_GRACE_SECONDS:
        raise LicenseError('Tolerância offline de 24 horas encerrada. Conecte-se à internet.')
    state['last_clock_seen'] = max(now, seen)
    _save(state)
    return {'valid': True, 'revoked': False, 'expires_at': state['last_expires_at'], 'offline': True}


def validate():
    state = _load()
    token = state.get('activation_token')
    if not token:
        raise LicenseError('Este computador ainda não possui uma licença ativada.')
    if state.get('server_url') != server_url():
        raise LicenseError('O endereço do servidor mudou. Reative a licença no servidor correto.')
    try:
        result = _post('/api/licenses/validate', {'activation_token': token, 'device_id': device_id()})
    except LicenseError as exc:
        # Somente falhas de transporte permitem o modo offline.
        # Respostas HTTP 4xx/5xx e JSON inválido nunca autorizam acesso offline.
        if not isinstance(exc.__cause__, (urllib.error.URLError, TimeoutError, OSError)) or isinstance(exc.__cause__, urllib.error.HTTPError):
            raise
        return _offline_fallback(state)
    if result.get('valid') is not True or result.get('revoked') is True:
        raise LicenseError('Licença expirada, revogada ou inválida.')
    expiry = result.get('expires_at')
    expiry_ts = _expiry_timestamp(expiry)
    if expiry_ts is None or expiry_ts <= time.time():
        raise LicenseError('Validação online sem prazo de validade válido.')
    now = time.time()
    state['last_online_validation'] = now
    state['last_clock_seen'] = now
    state['last_expires_at'] = expiry
    _save(state)
    return result

def ensure_valid():
    return validate()

def startup_gate():
    """Bloqueia o início da interface antes de haver uma licença válida."""
    try:
        validate()
        return
    except LicenseError as exc:
        initial_error = str(exc)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.title('EditAI Videos JW — Ativação de licença')
        root.geometry('510x260')
        root.resizable(False, False)
        tk.Label(root, text='EditAI Videos JW — Licenciamento', font=('Segoe UI', 14, 'bold')).pack(pady=(18, 8))
        tk.Label(root, text='Informe a chave fornecida pelo administrador.').pack()
        key_var = tk.StringVar()
        entry = tk.Entry(root, textvariable=key_var, width=53, font=('Segoe UI', 10))
        entry.pack(pady=12)
        status = tk.StringVar(value=initial_error)
        tk.Label(root, textvariable=status, wraplength=470, fg='#9c3030').pack(pady=6)
        allowed = {'value': False}
        def submit():
            try:
                activate(key_var.get())
            except LicenseError as error:
                status.set(str(error))
            else:
                allowed['value'] = True
                root.destroy()
        tk.Button(root, text='Ativar e abrir editor', command=submit, width=28).pack(pady=8)
        entry.bind('<Return>', lambda event: submit())
        entry.focus_set()
        root.mainloop()
        if not allowed['value']:
            raise LicenseError('A ativação não foi concluída. Editor não iniciado.')
    except ImportError as exc:
        raise LicenseError('Interface de ativação Tkinter indisponível neste Python.') from exc
