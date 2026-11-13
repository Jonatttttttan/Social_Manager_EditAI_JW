
# -*- mode: python ; coding: utf-8 -*-
"""Build onedir Windows; inclui dados/metadata de dependencias que leem arquivos em runtime."""

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

block_cipher = None

packages = (
    'gradio',
    'gradio_client',
    'safehttpx',
    'groovy',
    'faster_whisper',
    'ctranslate2',
    'av',
    'tokenizers',
    'huggingface_hub',
    'onnxruntime',
)

datas, binaries, hiddenimports = [], [], []

for package in packages:
    p_datas, p_bins, p_hidden = collect_all(package)
    datas += p_datas
    binaries += p_bins
    hiddenimports += p_hidden

# Versoes de algumas bibliotecas sao lidas diretamente de arquivos,
# nao de metadata.
# collect_all coleta os recursos; inclusao explicita torna essa
# dependencia verificavel.
for package in ('safehttpx', 'groovy'):
    datas += collect_data_files(package, includes=['version.txt'])

# Inclui FFmpeg e FFprobe no executavel distribuido.
for name in ('ffmpeg', 'ffprobe'):
    executable = Path('bin') / (name + '.exe')

    if not executable.is_file():
        raise SystemExit(
            f'Falta o executavel obrigatorio: {executable}'
        )

    binaries.append((str(executable), 'bin'))

# Inclui os arquivos de musica do editor.
datas.append(('promptvideo/music', 'promptvideo/music'))

# Analise das dependencias.
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Empacotamento do codigo Python.
pyz = PYZ(a.pure)

# Configuracao do executavel Windows.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PromptVideoAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,

    # Desativa a janela preta do terminal.
    console=False,
)

# Montagem da distribuicao completa.
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='PromptVideoAI',
)
