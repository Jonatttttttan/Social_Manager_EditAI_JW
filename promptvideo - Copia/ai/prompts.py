import re, json, math, threading, subprocess
from promptvideo.core.media import normalizar
from promptvideo.config import USAR_QWEN, MODELO_QWEN
def _tem(texto, padroes):
    return any(re.search(p, texto) for p in padroes)


def interpretar_regras(prompt):
    """Interpretação leve, offline, de pedidos de edição em português.

    Reconhece intenções e parâmetros; não inventa cortes ou frases.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('Digite uma instrução de edição.')
    t = normalizar(prompt).lower()
    plano = {'silencios': False, 'minimo': 1.0, 'limite_db': -35.,
             'margem': 0.15, 'ruido': 'nenhum', 'frases': [],
             'revisar_falas': False, 'melhorar_audio': False, 'duracao_alvo': None}

    # Evita interpretar pedidos explicitamente negados como operações.
    sem_silencio = _tem(t, [r'\b(?:nao|sem)\s+(?:remov\w*|cort\w*|tir\w*|mex\w*)\s+(?:\w+\s+){0,3}?(?:pausas?|silencios?)',
                            r'\b(?:mantenha|preserve|deixe)\s+(?:as?\s+)?(?:pausas?|silencios?)'])
    silencio = _tem(t, [
        r'\b(?:remov\w*|tir\w*|cort\w*|elimin\w*|apag\w*|exclu\w*|retir\w*|limp\w*)\s+(?:\w+\s+){0,5}?(?:silencios?|pausas?|intervalos?\s+sem\s+fala)',
        r'\b(?:silencios?|pausas?)\s+(?:long\w*|grand\w*|desnecessari\w*|excessiv\w*|maiores?)',
        r'\b(?:momentos?|trechos?|partes?)\s+(?:em\s+que\s+)?(?:eu\s+)?(?:nao\s+(?:falo|estou\s+falando)|sem\s+(?:fala|voz|som))',
        r'\b(?:encurt\w*|reduz\w*)\s+(?:\w+\s+){0,3}?(?:pausas?|silencios?)',
    ])
    plano['silencios'] = bool(silencio and not sem_silencio)

    # Limiar apenas quando associado a pausa/silêncio; '2 segundos' isolado não aciona cortes.
    m = re.search(r'(?:maior(?:es)?\s+(?:que|de)|mais\s+de|acima\s+de|pass\w*\s+de|superior(?:es)?\s+a)\s*(\d+(?:[.,]\d+)?)\s*(?:s\b|segundos?\b)', t)
    if not m:
        m = re.search(r'(?:pausas?|silencios?)\s+(?:de|com|acima\s+de)\s*(\d+(?:[.,]\d+)?)\s*(?:s\b|segundos?\b)', t)
    if m:
        plano['minimo'] = float(m.group(1).replace(',', '.'))

    m = re.search(r'(-?\d+(?:[.,]\d+)?)\s*db\b', t)
    if m:
        plano['limite_db'] = float(m.group(1).replace(',', '.'))

    ruido = _tem(t, [r'\b(?:ruido|chiado|zumbido|barulho|interferencia|ventilador|som\s+de\s+fundo|audio\s+sujo)\b'])
    # Se mencionar ruído como algo a preservar, não aplicar redução.
    preservar_ruido = _tem(t, [r'\b(?:nao\s+(?:reduz\w*|remov\w*|tir\w*|limp\w*)|mantenha|preserve)\s+(?:\w+\s+){0,3}?(?:ruido|chiado|barulho)'])
    if ruido and not preservar_ruido:
        plano['ruido'] = 'forte' if _tem(t, [r'\b(?:fortemente|intensamente|ruido\s+forte|barulho\s+forte)\b']) else 'medio'

    plano['revisar_falas'] = _tem(t, [
        r'\b(?:falas?\s+erradas?|erros?\s+de\s+fala|gaguej\w*|repeticoes?|trechos?\s+indesejados?)\b',
        r'\b(?:revis\w*|identifiq\w*|encontr\w*)\s+(?:\w+\s+){0,3}?(?:falas?|erros?\s+de\s+fala)'])

    # Melhoria de áudio já ocorre automaticamente na exportação da v0.3.
    plano['melhorar_audio'] = _tem(t, [
        r'\b(?:melhor\w*|aument\w*|normaliz\w*|uniformiz\w*|equaliz\w*|ajust\w*)\s+(?:\w+\s+){0,5}?(?:audio|som|voz|volume)',
        r'\b(?:voz|audio|som|volume)\s+(?:mais\s+)?(?:alt\w*|clar\w*|limp\w*|uniform\w*)',
        r'\b(?:deix\w*|torn\w*)\s+(?:\w+\s+){0,5}?(?:voz|audio|som)\s+(?:\w+\s+){0,3}?(?:melhor|mais\s+claro|mais\s+alto)',
    ])

    # Smart Duration Free: só reconhece duração quando vinculada a um pedido de edição.
    # Evita confundir duração do original ("meu vídeo tem 20 minutos") com a meta.
    alvo = re.search(
        r'\b(?:deix\w*|reduz\w*|encurt\w*|transform\w*|ajust\w*|fa[cç]a|fic\w*|dur\w*)'
        r'\s+(?:\w+\s+){0,9}?(?:para|com|em|de|ter|durar)\s+'
        r'(\d+(?:[.,]\d+)?)\s*(horas?|h\b|minutos?|mins?\b|m\b|segundos?|segs?\b|s\b)', t)
    if not alvo:
        alvo = re.search(r'\b(?:duracao|tempo)\s+(?:final|desejad\w*|de)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(horas?|h\b|minutos?|mins?\b|m\b|segundos?|segs?\b|s\b)',t)
    if alvo:
        quantidade = float(alvo.group(1).replace(',', '.'))
        unidade = alvo.group(2)
        fator = 3600 if unidade.startswith(('hora','h')) else (60 if unidade.startswith(('min','m')) else 1)
        plano['duracao_alvo'] = quantidade * fator

    # Frases entre aspas: só extrair quando houver verbo de remoção no contexto.
    for match in re.finditer(r'["“]([^"”\n]{1,200})["”]', prompt):
        antes = normalizar(prompt[max(0, match.start()-120):match.start()]).lower()
        if _tem(antes, [r'\b(?:remov\w*|cort\w*|exclu\w*|tir\w*|apag\w*|retir\w*|elimin\w*)\b']):
            frase = match.group(1).strip()
            if frase and frase not in plano['frases']:
                plano['frases'].append(frase)
    return validar_plano(plano)

def validar_plano(p):
    if not isinstance(p,dict):raise ValueError('Plano inválido')
    plano={'silencios':bool(p.get('silencios',False)),'ruido':p.get('ruido','nenhum'), 'revisar_falas':bool(p.get('revisar_falas',False)), 'melhorar_audio':bool(p.get('melhorar_audio',False)), 'duracao_alvo':p.get('duracao_alvo')}
    if plano['ruido'] not in ('nenhum','leve','medio','forte'):raise ValueError('Ruído inválido')
    for nome,lo,hi,padrao in [('minimo',0.1,30.,1.),('limite_db',-90.,-5.,-35.),('margem',0.,1.,0.15)]:
        valor=p.get(nome,padrao)
        if isinstance(valor,bool) or not isinstance(valor,(int,float)) or not math.isfinite(valor) or not lo<=valor<=hi:raise ValueError(f'{nome} fora do intervalo [{lo},{hi}]')
        plano[nome]=float(valor)
    alvo=plano['duracao_alvo']
    if alvo is not None and (isinstance(alvo,bool) or not isinstance(alvo,(int,float)) or not math.isfinite(alvo) or not 1<=alvo<=86400):
        raise ValueError('Duração desejada deve estar entre 1 segundo e 24 horas')
    frases=p.get('frases',[])
    if not isinstance(frases,list) or len(frases)>30 or any(not isinstance(x,str) or len(x)>200 for x in frases):raise ValueError('Frases inválidas')
    plano['frases']=[x.strip() for x in frases if x.strip()]
    if not (plano['silencios'] or plano['ruido']!='nenhum' or plano['frases'] or plano['revisar_falas'] or plano['melhorar_audio'] or plano['duracao_alvo'] is not None):
        raise ValueError('Pedido não reconhecido. Ex.: Remova silêncios, reduza ruído e corte a frase "vou recomeçar".')
    return plano

_qwen=None; _tokenizer=None
_lock_qwen=threading.Lock()
def interpretar_qwen(prompt):
    global _qwen,_tokenizer
    with _lock_qwen:
        import torch
        if not torch.cuda.is_available():raise RuntimeError('Qwen requer GPU CUDA; use o interpretador leve ou ative GPU T4.')
        try:
            from transformers import AutoTokenizer,AutoModelForCausalLM
        except ImportError:
            raise RuntimeError('Instale o extra qwen para habilitar o modelo')
        if _qwen is None:
            _tokenizer=AutoTokenizer.from_pretrained(MODELO_QWEN)
            _qwen=AutoModelForCausalLM.from_pretrained(MODELO_QWEN,torch_dtype=torch.float16,device_map='cuda').eval()
        sistema=('Converta o pedido para JSON válido sem Markdown. Campos: silencios (boolean), minimo (0.1 a 30), limite_db (-90 a -5), margem (0 a 1), ruido (nenhum/leve/medio/forte), frases (lista de frases explicitamente pedidas para remover), revisar_falas (boolean), melhorar_audio (boolean). Não invente frases; pedidos vagos sobre falas erradas apenas ativam revisar_falas. Não proponha operações além dessas.')
        msgs=[{'role':'system','content':sistema},{'role':'user','content':prompt}]
        entrada=_tokenizer.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,return_tensors='pt').to('cuda')
        with torch.inference_mode():saida=_qwen.generate(entrada,max_new_tokens=220,do_sample=False,pad_token_id=_tokenizer.eos_token_id)
        resposta=_tokenizer.decode(saida[0][entrada.shape[-1]:],skip_special_tokens=True)
        m=re.search(r'\{.*\}',resposta,re.S)
        if not m:raise ValueError('Qwen não retornou JSON: '+resposta[:250])
        return validar_plano(json.loads(m.group()))

def interpretar_prompt(prompt):
    if USAR_QWEN:
        try:return interpretar_qwen(prompt)
        except Exception as e:
            print('Qwen indisponível; usando regras:',e)
    return interpretar_regras(prompt)
