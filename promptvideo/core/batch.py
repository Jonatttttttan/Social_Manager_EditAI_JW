"""Fila sequencial de edições; falhas isoladas por arquivo."""
import json
import zipfile
from datetime import datetime
from pathlib import Path
from promptvideo.config import SAIDAS
from promptvideo.core.jobs import preparar_video, aplicar_proposta
from promptvideo.ai.prompts import validar_plano
from promptvideo.core.media import FORMATOS_ENTRADA
from promptvideo.core.transitions import validar_transicao
from promptvideo.features.background_music import adicionar_musica, escolher_musica, validar_volume
from promptvideo.features.video_filters import validar_filtros, aplicar_filtro_video
from promptvideo.features.subtitles import legendar_video, validar_aparencia

MAX_VIDEOS = 20

def validar_lote(arquivos, instrucao, estilo):
    if not arquivos:
        raise ValueError('Selecione ao menos um vídeo MP4 ou MOV.')
    if len(arquivos) > MAX_VIDEOS:
        raise ValueError(f'O limite por lote é {MAX_VIDEOS} vídeos.')
    if isinstance(instrucao, dict):
        validar_plano(instrucao)
    elif not isinstance(instrucao, str) or not instrucao.strip():
        raise ValueError('Selecione pelo menos uma opção de edição.')
    if estilo not in ('Tradicional', 'Dinâmica'):
        raise ValueError('Estilo de legenda inválido.')
    caminhos = [Path(a) for a in arquivos]
    if any(not p.is_file() or p.suffix.lower() not in FORMATOS_ENTRADA for p in caminhos):
        raise ValueError('Todos os arquivos devem ser vídeos MP4 ou MOV válidos.')
    return caminhos

def executar_lote(arquivos, instrucao, legendas=False, estilo='Tradicional', callback=None, status_callback=None, visual='Clássica', tamanho=100, posicao='Inferior', transicao='Nenhuma', duracao_transicao=0.7, trilha='Sem música', arquivo_musica=None, volume_musica=20, manter_audio=True, fade_musica=True, filtro_video='Original', intensidade_filtro=60, brilho_filtro=0, contraste_filtro=0, transicoes=None):
    from promptvideo.features.subtitle_storage import (
        normalizar_config_transicoes,
    )

    from promptvideo.features.edge_transitions import (
        aplicar_transicoes_extremidades,
    )

    usar_novas_transicoes = transicoes is not None

    transicoes = normalizar_config_transicoes(transicoes)

    if usar_novas_transicoes:
        transicao = "Nenhuma"

    caminhos = validar_lote(arquivos, instrucao, estilo)
    validar_aparencia(visual,tamanho,posicao)
    validar_transicao(transicao,duracao_transicao)
    escolher_musica(trilha,arquivo_musica)
    validar_volume(volume_musica)
    validar_filtros(filtro_video,intensidade_filtro,brilho_filtro,contraste_filtro)
    registros=[]
    def emitir(indice, fracao, etapa, status='processando'):
        if status_callback: status_callback(indice-1, max(0.,min(1.,float(fracao))), etapa, status)
    for indice, caminho in enumerate(caminhos, 1):
        if callback: callback(indice, len(caminhos), caminho.name)
        emitir(indice, 0, 'Iniciando análise')
        registro={'arquivo':caminho.name, 'status':'erro', 'saida':None, 'srt':None, 'erro':None}
        try:
            identificador, proposta=preparar_video(str(caminho), instrucao, callback=lambda p,s: emitir(indice, .20*p, s))
            # Lote automático: aprova somente cortes calculados por regras determinísticas.
            resultado=aplicar_proposta(identificador,json.dumps(proposta['cortes'],ensure_ascii=False),callback=lambda p,s: emitir(indice,.20+(.55 if legendas else .78)*p,s),transicao=transicao,duracao_transicao=duracao_transicao)
            if legendas:
                resultado,srt=legendar_video(resultado,estilo,callback=lambda p,s: emitir(indice,.75+.23*p,s),visual=visual,tamanho=tamanho,posicao=posicao)
                registro['srt']=str(srt)
            resultado=adicionar_musica(resultado,trilha,arquivo_musica,volume_musica,manter_audio,fade_musica,callback=lambda msg: emitir(indice,.99,msg))
            resultado=aplicar_filtro_video(resultado,filtro_video,intensidade_filtro,brilho_filtro,contraste_filtro,callback=lambda msg: emitir(indice,.995,msg))
            resultado = aplicar_transicoes_extremidades(
                resultado,
                **transicoes,
                callback=lambda msg: emitir(indice, .997, msg)
            )

            registro['saida']=str(resultado)
            registro['status']='concluido'
            emitir(indice, 1.0, 'Concluído', 'concluido')
        except Exception as exc:
            registro['erro']=f'{type(exc).__name__}: {exc}'
            emitir(indice, 1.0, 'Erro: '+str(exc)[:100], 'erro')
        registros.append(registro)
    # Identificador com resolução em microssegundos; não sobrescreve arquivos anteriores.
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    pacote=SAIDAS / f'lote_{stamp}.zip'
    relatorio={'instrucoes':instrucao,'legendas':bool(legendas),'estilo':estilo,'visual':visual,'tamanho':tamanho,'posicao':posicao,'transicao':transicao,'duracao_transicao':float(duracao_transicao),'trilha':trilha,'volume_musica':float(volume_musica),'manter_audio':bool(manter_audio),'fade_musica':bool(fade_musica),'filtro_video':filtro_video,'intensidade_filtro':float(intensidade_filtro),'brilho_filtro':float(brilho_filtro),'contraste_filtro':float(contraste_filtro),'itens':registros}
    relatorio["transicoes"] = transicoes

    with zipfile.ZipFile(pacote,'w',compression=zipfile.ZIP_DEFLATED) as z:
        nomes_usados = {'relatorio.json'}
        for registro in registros:
            for campo in ('srt', 'saida'):
                campo_zip = campo + '_zip'
                registro[campo_zip] = None
                caminho = registro.get(campo)
                if not caminho:
                    continue
                arquivo = Path(caminho)
                if not arquivo.is_file():
                    continue
                nome = arquivo.name
                contador = 2
                while nome.casefold() in nomes_usados:
                    nome = f'{arquivo.stem}_{contador}{arquivo.suffix}'
                    contador += 1
                z.write(arquivo, arcname=nome)
                nomes_usados.add(nome.casefold())
                registro[campo_zip] = nome
        z.writestr('relatorio.json',json.dumps(relatorio,ensure_ascii=False,indent=2))
    return str(pacote), registros
