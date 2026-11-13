import os, tempfile, math
from pathlib import Path
from promptvideo.config import THREADS_FFMPEG, CRF_VIDEO, PRESET_VIDEO, MAX_TRECHOS
from promptvideo.core.media import analisar_video, trechos_preservados, executar, ffmpeg_bin
from promptvideo.core.transitions import validar_transicao, unir_com_transicoes
from promptvideo.features.audio import filtro_ruido
from promptvideo.features.audio_enhancer import melhorar_audio
def renderizar_edicao(caminho_entrada, caminho_saida, cortes, ruido='nenhum', callback=None, transicao='Nenhuma', duracao_transicao=0.7):
    origem=Path(caminho_entrada); destino=Path(caminho_saida)
    info=analisar_video(origem)
    dur=info['duracao']
    intervalos=[]
    for c in cortes:
        if not isinstance(c,dict):raise ValueError('Cada corte precisa ser um objeto com inicio e fim')
        a,b=float(c['inicio']),float(c['fim'])
        if not all(math.isfinite(x) for x in (a,b)) or a<0 or b>dur+0.1 or b<=a:raise ValueError(f'Corte inválido: {c}')
        intervalos.append((a,min(b,dur)))
    manter=trechos_preservados(intervalos,dur)
    if not manter:raise ValueError('Os cortes removeriam todo o vídeo; revise a proposta.')
    if len(manter)>MAX_TRECHOS:raise ValueError('Trechos demais; reduza os cortes ou divida o vídeo.')
    duracao_transicao=validar_transicao(transicao,duracao_transicao)
    if transicao != 'Nenhuma' and len(manter)>1 and duracao_transicao>=min(b-a for a,b in manter)-0.08:
        raise ValueError('A transição é maior que um dos trechos preservados. Diminua sua duração.')
    filtro=filtro_ruido(ruido)
    if ruido!='nenhum' and not filtro:raise ValueError('Nível de ruído inválido')
    destino.parent.mkdir(parents=True,exist_ok=True)
    fps=info['fps']
    # FPS compatível entre segmentos, sem fixar 30 para todos os vídeos.
    fps=max(1,min(120,round(fps,3)))
    with tempfile.TemporaryDirectory(prefix='promptvideo_',dir=str(destino.parent)) as tmp:
        tmp=Path(tmp); arquivos=[]
        for i,(inicio,fim) in enumerate(manter,1):
            if callback: callback(0.05 + 0.72*(i-1)/len(manter), f'Codificando trecho {i} de {len(manter)}')
            print(f'[{i}/{len(manter)}] {inicio:.2f}s a {fim:.2f}s',flush=True)
            arq=tmp/f'trecho_{i:04d}.mp4'
            cmd=[ffmpeg_bin('ffmpeg'),'-y','-hide_banner','-nostdin','-nostats','-threads',str(THREADS_FFMPEG),
                 '-ss',f'{inicio:.6f}','-i',str(origem),'-t',f'{fim-inicio:.6f}',
                 '-map','0:v:0']
            if info['possui_audio']:cmd+=['-map','0:a:0']
            else:cmd+=['-an']
            cmd+=['-c:v','libx264','-threads',str(THREADS_FFMPEG),'-preset',PRESET_VIDEO,
                  '-crf',str(CRF_VIDEO),'-pix_fmt','yuv420p','-r',str(fps)]
            if info['possui_audio']:
                if filtro:cmd+=['-af',filtro]
                cmd+=['-c:a','aac','-b:a','128k','-ar','48000','-ac','2']
            cmd+=['-avoid_negative_ts','make_zero',str(arq)]
            executar(cmd,f'Trecho {i}',tmp/f'trecho_{i:04d}.log')
            if not arq.is_file() or arq.stat().st_size==0:raise RuntimeError(f'Trecho {i} vazio')
            arquivos.append(arq)
            if callback: callback(0.05 + 0.72*i/len(manter), f'Trecho {i} de {len(manter)} concluído')
        if transicao != 'Nenhuma' and len(arquivos)>1:
            if callback: callback(0.79, 'Aplicando transições entre cortes')
            parcial=tmp/'final.mp4'
            unir_com_transicoes(arquivos,[b-a for a,b in manter],parcial,transicao,duracao_transicao,fps,info['possui_audio'],tmp)
        else:
            lista=tmp/'lista.txt'
            lista.write_text(''.join("file '"+p.name+"'\n" for p in arquivos),encoding='utf-8')
            parcial=tmp/'final.mp4'
            cmd=[ffmpeg_bin('ffmpeg'),'-y','-hide_banner','-nostdin','-nostats','-f','concat','-safe','0','-i',str(lista),'-c','copy','-movflags','+faststart',str(parcial)]
            if callback: callback(0.79, 'Unindo trechos')
            executar(cmd,'Concatenação',tmp/'concat.log')
        if not parcial.is_file() or parcial.stat().st_size==0:raise RuntimeError('Saída vazia')
        # Pós-processamento automático apenas uma vez, após juntar os trechos.
        # O arquivo original e o vídeo intermediário ficam intactos em caso de erro.
        if info['possui_audio']:
            aprimorado=tmp/'final_audio_melhorado.mp4'
            if callback: callback(0.86, 'Melhorando áudio')
            melhorar_audio(parcial, aprimorado)
            os.replace(aprimorado,destino)
        else:
            os.replace(parcial,destino)
    if callback: callback(1.0, 'Vídeo editado')
    return destino
