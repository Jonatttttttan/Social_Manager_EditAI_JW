"""Smart Duration Free: encurta apenas silêncios, sem transcrição ou LLM."""
import math
from promptvideo.core.media import juntar_intervalos


def planejar_duracao(duracao, alvo, cortes_existentes, silencios, margem=0.12):
    """Retorna (cortes, metadados). Cortes são intervalos a REMOVER.

    Não corta fala para forçar uma duração exata. Pausas são aparadas do centro,
    mantendo margens de segurança em ambas as extremidades.
    """
    if not math.isfinite(duracao) or duracao <= 0 or not math.isfinite(alvo) or alvo <= 0:
        raise ValueError('Duração inválida')
    base = juntar_intervalos(cortes_existentes, duracao)
    removido = sum(b-a for a,b in base)
    atual = duracao-removido
    faltam = max(0.,atual-alvo)
    candidatos=[]
    for inicio,fim in silencios:
        if not (math.isfinite(inicio) and math.isfinite(fim)):
            continue
        # Os intervalos de silêncio já possuem margem protetora do detector.
        a=max(0.,inicio); b=min(duracao,fim)
        if b-a < 0.15:
            continue
        # Retira trechos já marcados para corte, sem duplicar duração removida.
        partes=[(a,b)]
        for x,y in base:
            novas=[]
            for u,v in partes:
                if y<=u or x>=v:novas.append((u,v))
                else:
                    if x-u>0.01:novas.append((u,x))
                    if v-y>0.01:novas.append((y,v))
            partes=novas
        for u,v in partes:
            if v-u>=0.15:candidatos.append((u,v))
    # Pausas longas primeiro; evita fragmentar fala.
    candidatos.sort(key=lambda x:x[1]-x[0],reverse=True)
    adicionais=[]
    for a,b in candidatos:
        if faltam<=0.015:break
        disponivel=b-a
        retirar=min(disponivel,faltam)
        centro=(a+b)/2
        adicionais.append((centro-retirar/2,centro+retirar/2))
        faltam-=retirar
    todos=juntar_intervalos(base+adicionais,duracao)
    final=duracao-sum(b-a for a,b in todos)
    return todos, {'original':duracao,'alvo':alvo,'estimada':max(0.,final),
                   'atingida':abs(final-alvo)<=0.15,'limitacao':
                   ('Não há silêncio suficiente para atingir a duração sem remover falas.' if final>alvo+0.15 else
                    'A duração já era menor que a solicitada; não alongamos o vídeo.' if atual<alvo-0.15 else '')}
