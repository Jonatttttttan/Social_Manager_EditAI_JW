import os, re, json, shutil, threading
from pathlib import Path
from promptvideo.config import ENTRADAS, SAIDAS, RESERVAS
from promptvideo.core.planning import montar_proposta
from promptvideo.core.render import renderizar_edicao
from promptvideo.core.manual_cuts import interpretar_cortes_manuais, combinar_cortes
from promptvideo.core.media import analisar_video
from promptvideo.core.media import validar_extensao_video, FORMATOS_ENTRADA
_lock_nomes = threading.Lock()

def reservar_identificador():
    # O_CREAT|O_EXCL garante que duas requisições não reservem o mesmo nome.
    with _lock_nomes:
        existentes = []
        for pasta in (ENTRADAS, SAIDAS, RESERVAS):
            for arquivo in pasta.glob('video_*'):
                m = re.match(r'^video_(\d+)', arquivo.name)
                if m:
                    existentes.append(int(m.group(1)))
        numero = max(existentes, default=0) + 1
        while True:
            identificador = f'video_{numero:04d}'
            reserva = RESERVAS / f'{identificador}.lock'
            try:
                fd = os.open(reserva, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
                return identificador
            except FileExistsError:
                numero += 1

def salvar_video_entrada(caminho_temporario):
    origem = Path(caminho_temporario)
    if not origem.is_file():
        raise FileNotFoundError(origem)
    # O Gradio pode converter para MP4; a extensão não é prova de formato.
    validar_extensao_video(origem)
    # Valida a mídia de fato antes de aceitar um arquivo renomeado.
    from promptvideo.core.media import analisar_video
    analisar_video(origem)
    identificador = reservar_identificador()
    destino = ENTRADAS / f'{identificador}{origem.suffix.lower()}'
    shutil.copy2(origem, destino)
    return identificador, destino

# A proposta é associada ao caminho da cópia original, não a um caminho arbitrário enviado pelo usuário.
_propostas={}
_lock_propostas=threading.Lock()
PROPOSTAS = RESERVAS / 'propostas'
PROPOSTAS.mkdir(exist_ok=True)


def preparar_video(caminho_temporario,prompt,callback=None):
    identificador,entrada=salvar_video_entrada(caminho_temporario)
    if callback: callback(0.1, 'Analisando vídeo e áudio')
    proposta=montar_proposta(entrada,prompt)
    if callback: callback(1.0, 'Análise concluída')
    with _lock_propostas:
        _propostas[identificador]={'entrada':entrada,'proposta':proposta}
        (PROPOSTAS / f'{identificador}.json').write_text(json.dumps(proposta,ensure_ascii=False),encoding='utf-8')
    return identificador,proposta

def aplicar_proposta(identificador,cortes_json,callback=None,transicao='Nenhuma',duracao_transicao=0.7, cortes_manuais=''):
    with _lock_propostas:registro=_propostas.get(identificador)
    if not registro:
        if not re.fullmatch(r'video_\d{4,}', str(identificador)):
            raise ValueError('Identificador inválido')
        proposta_path = PROPOSTAS / f'{identificador}.json'
        entradas = [ENTRADAS / f'{identificador}{ext}' for ext in sorted(FORMATOS_ENTRADA)]
        entrada = next((p for p in entradas if p.is_file()), None)
        if not proposta_path.is_file() or entrada is None:
            raise ValueError('Proposta não encontrada. Analise o vídeo novamente.')
        registro={'entrada':entrada,'proposta':json.loads(proposta_path.read_text(encoding='utf-8'))}
    proposta=registro['proposta']
    cortes=json.loads(cortes_json)
    if not isinstance(cortes,list):raise ValueError('Cortes devem ser uma lista JSON')
    duracao=analisar_video(registro['entrada'])['duracao']
    manuais=interpretar_cortes_manuais(cortes_manuais,duracao)
    cortes=combinar_cortes(cortes,manuais)
    saida=SAIDAS/f'{identificador}_editado.mp4'
    final=renderizar_edicao(registro['entrada'],saida,cortes,proposta['plano']['ruido'],callback=callback,transicao=transicao,duracao_transicao=duracao_transicao,melhorar_audio_habilitado=proposta['plano'].get('melhorar_audio', True))
    return str(final)
