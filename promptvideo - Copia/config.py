import os
from pathlib import Path
BASE = Path(os.environ.get('PROMPTVIDEO_DATA', str(Path.home() / 'PromptVideoAI'))).expanduser().resolve()
ENTRADAS = BASE / 'entradas'
SAIDAS = BASE / 'saidas'
RESERVAS = BASE / 'reservas'
for p in (ENTRADAS, SAIDAS, RESERVAS):
    p.mkdir(parents=True, exist_ok=True)
THREADS_FFMPEG = 2
CRF_VIDEO = 25
PRESET_VIDEO = 'veryfast'
MAX_TRECHOS = 250
MODELO_WHISPER = os.getenv('PROMPTVIDEO_WHISPER', 'base')
USAR_QWEN = os.getenv('PROMPTVIDEO_QWEN', '0') == '1'
MODELO_QWEN = 'Qwen/Qwen2.5-1.5B-Instruct'
