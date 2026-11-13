"""Intervalos manuais de exclusão, sempre em relação ao vídeo ORIGINAL."""
import json
import math
import re

MAX_CORTES_MANUAIS = 100

def tempo_em_segundos(texto):
    if not isinstance(texto, str):
        raise ValueError('Horário inválido.')
    partes = texto.strip().split(':')
    if len(partes) not in (2, 3) or any(not re.fullmatch(r'\d+', p) for p in partes):
        raise ValueError('Use MM:SS ou HH:MM:SS.')
    nums = list(map(int, partes))
    if nums[-1] >= 60 or (len(nums) == 3 and nums[-2] >= 60):
        raise ValueError('Segundos e minutos devem ser menores que 60.')
    return nums[0]*60+nums[1] if len(nums)==2 else nums[0]*3600+nums[1]*60+nums[2]

def interpretar_cortes_manuais(texto, duracao):
    """Linhas no formato 00:02:30 - 00:03:15; devolve cortes normalizados."""
    if not texto or not str(texto).strip():
        return []
    if not math.isfinite(float(duracao)) or duracao <= 0:
        raise ValueError('Duração do vídeo inválida.')
    linhas = [l.strip() for l in str(texto).splitlines() if l.strip()]
    if len(linhas) > MAX_CORTES_MANUAIS:
        raise ValueError('Limite de 100 intervalos manuais.')
    cortes=[]
    for numero, linha in enumerate(linhas, 1):
        pedacos = re.split(r'\s*[-–—]\s*', linha)
        if len(pedacos) != 2:
            raise ValueError(f'Linha {numero}: use início - fim (ex.: 02:30 - 03:15).')
        try:
            inicio, fim = map(tempo_em_segundos, pedacos)
        except ValueError as exc:
            raise ValueError(f'Linha {numero}: {exc}') from exc
        if inicio >= fim or fim > duracao + 0.05:
            raise ValueError(f'Linha {numero}: intervalo fora do vídeo ou início >= fim (duração {duracao:.1f}s).')
        cortes.append({'inicio':float(inicio), 'fim':float(min(fim, duracao))})
    return cortes

def combinar_cortes(cortes_automaticos, cortes_manuais):
    """União dos cortes; intervalos sobrepostos ou adjacentes são fundidos."""
    todos=[]
    for item in [*cortes_automaticos, *cortes_manuais]:
        a,b=float(item['inicio']),float(item['fim'])
        if not math.isfinite(a) or not math.isfinite(b) or a < 0 or b <= a:
            raise ValueError('Intervalo de corte inválido.')
        todos.append((a,b))
    todos.sort()
    unidos=[]
    for a,b in todos:
        if unidos and a <= unidos[-1][1] + 0.000001:
            unidos[-1] = (unidos[-1][0],max(b,unidos[-1][1]))
        else:
            unidos.append((a,b))
    return [{'inicio':a,'fim':b} for a,b in unidos]
