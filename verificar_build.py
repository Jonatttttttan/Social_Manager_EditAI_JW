"""Verificacao estatica do onedir; nao substitui execucao real no Windows."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parent/'dist'/'PromptVideoAI'
required=[root/'PromptVideoAI.exe', root/'_internal'/'safehttpx'/'version.txt', root/'_internal'/'groovy'/'version.txt', root/'_internal'/'bin'/'ffmpeg.exe', root/'_internal'/'bin'/'ffprobe.exe']
for path in required:
    print(('OK' if path.is_file() else 'FALTA'),path)
if any(not p.is_file() for p in required):
    sys.exit(1)
print('Arquivos essenciais presentes. Execute o EXE para testar imports, interface e exportacao.')
