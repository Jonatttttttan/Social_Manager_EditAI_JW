import re
from promptvideo.core.media import analisar_video, normalizar
from promptvideo.ai.prompts import interpretar_prompt, validar_plano
from promptvideo.features.audio import detectar_silencios, transcrever
from promptvideo.core.duration import planejar_duracao
from promptvideo.core.media import juntar_intervalos
def encontrar_frases(segmentos, frases):
    palavras=[]
    for s in segmentos:
        for w in s.get('palavras',[]):
            token=normalizar(w['texto'])
            token=re.sub(r'[^a-z0-9]+','',token)
            if token:palavras.append((token,w['inicio'],w['fim']))
    resultados=[]; nao_encontradas=[]
    for frase in frases:
        tokens=[re.sub(r'[^a-z0-9]+','',normalizar(x)) for x in frase.split()]
        tokens=[x for x in tokens if x]
        matches=[]
        if tokens:
            for i in range(len(palavras)-len(tokens)+1):
                if [w[0] for w in palavras[i:i+len(tokens)]]==tokens:
                    matches.append((palavras[i][1],palavras[i+len(tokens)-1][2]))
        if matches:
            for a,b in matches:resultados.append({'inicio':round(a,3),'fim':round(b,3),'motivo':'Frase: '+frase})
        else:nao_encontradas.append(frase)
    return resultados,nao_encontradas

def montar_proposta(video,prompt):
    info=analisar_video(video)
    plano = validar_plano(prompt) if isinstance(prompt, dict) else interpretar_prompt(prompt)
    if not info['possui_audio']:
        raise ValueError('Vídeo sem áudio: operações de silêncio, transcrição e redução de ruído não se aplicam.')
    cortes=[]; transcricao=[]; nao_encontradas=[]
    if plano['silencios'] and plano['duracao_alvo'] is None:
        for a,b in detectar_silencios(video,info['duracao'],plano['limite_db'],plano['minimo'],plano['margem']):
            cortes.append({'inicio':round(a,3),'fim':round(b,3),'motivo':'Silêncio'})
    if plano['frases'] or plano['revisar_falas']:
        transcricao=transcrever(video)
        encontrados,nao_encontradas=encontrar_frases(transcricao,plano['frases'])
        cortes.extend(encontrados)
    duracao_info=None
    if plano['duracao_alvo'] is not None:
        # Intervalos explícitos de remoção continuam prioritários.
        # Não há cortes semânticos automáticos na edição Free.
        existentes=[(c['inicio'],c['fim']) for c in cortes]
        pausas=detectar_silencios(video,info['duracao'],plano['limite_db'],0.35,0.12)
        novos,duracao_info=planejar_duracao(info['duracao'],plano['duracao_alvo'],existentes,pausas)
        cortes=[{'inicio':round(a,3),'fim':round(b,3),'motivo':'Smart Duration / corte existente'} for a,b in novos]
    # Nenhuma inferência subjetiva de 'erro': o usuário revisa a transcrição.
    return {'plano':plano,'duracao':info['duracao'],'fps':info['fps'],
            'cortes':cortes,'duracao_info':duracao_info,'transcricao':transcricao,'frases_nao_encontradas':nao_encontradas,
            'observacao':'Cortes por frase são aproximados. Revise antes de aplicar; falas erradas não são removidas sem identificação explícita.'}
