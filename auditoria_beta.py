"""Auditoria estatica e offline da distribuicao; nao substitui testes Windows."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CHECKS = {
    'Entrada Python': ROOT / 'main.py',
    'Interface Gradio': ROOT / 'promptvideo/ui/gradio_app.py',
    'Estilos de legenda': ROOT / 'promptvideo/features/subtitles.py',
    'Spec PyInstaller': ROOT / 'PromptVideoAI.spec',
    'Instalador Inno Setup': ROOT / 'installer.iss',
    'Verificador do build': ROOT / 'verificar_build.py',
    'FFmpeg (instrucoes)': ROOT / 'bin/README.txt',
}

def auditar():
    problemas = []
    for nome, arquivo in CHECKS.items():
        existe = arquivo.is_file()
        print(f"{'OK' if existe else 'FALTA'}: {nome} - {arquivo.relative_to(ROOT)}")
        if not existe:
            problemas.append(nome)
    iss = (ROOT / 'installer.iss').read_text(encoding='utf-8') if (ROOT / 'installer.iss').is_file() else ''
    for marcador in ('EditAI Videos JW', '0.9.0-beta', 'EditAI-Videos-JW-0.9.0-beta-Setup'):
        if marcador not in iss:
            problemas.append('Identidade do instalador: ' + marcador)
    build = ROOT / 'dist' / 'PromptVideoAI'
    if build.exists():
        for rel in ('PromptVideoAI.exe', '_internal/safehttpx/version.txt', '_internal/groovy/version.txt', '_internal/bin/ffmpeg.exe', '_internal/bin/ffprobe.exe'):
            if not (build / rel).is_file():
                problemas.append('Build incompleto: ' + rel)
    else:
        print('AVISO: dist nao existe; build Windows ainda nao verificado.')
    for problema in problemas:
        print('ERRO:', problema)
    print('Auditoria estatica:', 'APROVADA' if not problemas else 'REPROVADA')
    return not problemas

if __name__ == '__main__':
    sys.exit(0 if auditar() else 1)
