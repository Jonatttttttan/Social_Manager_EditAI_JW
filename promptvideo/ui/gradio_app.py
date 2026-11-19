import json, traceback, html, queue, threading, time
import hashlib
import webbrowser
from promptvideo.integrations.instagram_oauth_client import InstagramOAuthClientError, conectar_instagram, status_instagram, desconectar_instagram, preparar_reel_servidor, criar_container_reel, consultar_reel, publicar_reel_servidor
from pathlib import Path
import gradio as gr
from promptvideo.config import SAIDAS
from promptvideo.integrations.instagram import preparar_reel, publicar_reel, status_reel, InstagramPublishError
from promptvideo.licensing import ensure_valid, LicenseError
from promptvideo.core.jobs import preparar_video, aplicar_proposta
from promptvideo.core.batch import executar_lote
from promptvideo.features.subtitles import legendar_video, legendar_manual, ESTILOS_VISUAIS
from promptvideo.features.background_music import TRACKS, escolher_musica, adicionar_musica
from promptvideo.features.video_filters import FILTROS, aplicar_filtro_video
from promptvideo.features.zoom import aplicar_zoom
from promptvideo.features.sound_effects import EFFECTS, EFFECT_DIR, aplicar_efeitos

def interface_analisar(video,prompt):
    ensure_valid()
    try:
        if not video:raise ValueError('Envie um vídeo MP4 ou MOV')
        if not prompt or not prompt.strip():raise ValueError('Digite um pedido de edição')
        identificador,p=preparar_video(video,prompt)
        transcricao='\n'.join(f"[{s['inicio']:.2f}–{s['fim']:.2f}] {s['texto']}" for s in p['transcricao'])
        if not transcricao:transcricao='Transcrição não solicitada. Peça para remover uma frase ou revisar falas.'
        resumo=f"**{identificador}** | {p['duracao']:.1f}s | {len(p['cortes'])} cortes sugeridos | Ruído: {p['plano']['ruido']}"
        acoes=[]
        if p['plano']['silencios']: acoes.append(f"Remover silêncios a partir de {p['plano']['minimo']:g}s")
        if p['plano']['ruido']!='nenhum': acoes.append('Reduzir ruído de fundo')
        if p['plano']['frases']: acoes.append('Remover frases: '+', '.join(p['plano']['frases']))
        if p['plano']['revisar_falas']: acoes.append('Revisar falas na transcrição')
        acoes.append('Melhoria automática de áudio na exportação')
        resumo+='\n\n**Interpretação do pedido:**\n'+''.join('\n- '+a for a in acoes)
        if p.get('duracao_info'):
            d=p['duracao_info']
            resumo+=f"\n\n**Smart Duration Free:** original {d['original']:.1f}s → meta {d['alvo']:.1f}s → estimativa {d['estimada']:.1f}s."
            if d['limitacao']:resumo+='\n\n**Limitação:** '+d['limitacao']
            resumo+='\n\nA estimativa pode variar alguns segundos após a codificação. Revise os cortes.'
        if p['frases_nao_encontradas']:resumo+='\n\nFrases não localizadas: '+', '.join(p['frases_nao_encontradas'])
        if p['plano']['revisar_falas']:resumo+='\n\n**Revisão manual:** indique cortes adicionais editando o JSON; não há exclusão automática de falas subjetivamente erradas.'
        return identificador,resumo,json.dumps(p['cortes'],ensure_ascii=False,indent=2),transcricao
    except Exception as e:
        traceback.print_exc();raise gr.Error(str(e))

def interface_aplicar(identificador,cortes_json,ativar_legendas,estilo,visual="Clássica",tamanho=100,posicao="Inferior"):
    ensure_valid()
    try:
        if not identificador:raise ValueError('Clique primeiro em Analisar vídeo')
        caminho=aplicar_proposta(identificador,cortes_json)
        if ativar_legendas:
            legendado,srt=legendar_video(caminho,estilo,visual=visual,tamanho=tamanho,posicao=posicao)
            return legendado,legendado,srt,'Edição e legendas concluídas: '+Path(legendado).name
        return caminho,caminho,None,'Edição concluída: '+Path(caminho).name
    except Exception as e:
        traceback.print_exc();raise gr.Error(str(e))

def interface_lote(arquivos, instrucao, legendas, estilo, progress=gr.Progress(), visual="Clássica", tamanho=100, posicao="Inferior", transicao="Nenhuma", duracao_transicao=0.7):
    ensure_valid()
    try:
        def atualizar(i, total, nome):
            progress((i-1)/total, desc=f'Processando {i}/{total}: {nome}')
        pacote, registros=executar_lote(arquivos, instrucao, legendas, estilo, atualizar, visual=visual,tamanho=tamanho,posicao=posicao,transicao=transicao,duracao_transicao=duracao_transicao)
        progress(1.0, desc='Lote finalizado')
        ok=sum(r['status']=='concluido' for r in registros)
        linhas=[f"- **{r['arquivo']}**: " + ('Concluído' if r['status']=='concluido' else 'Erro — '+r['erro']) for r in registros]
        return pacote, f"**{ok}/{len(registros)} vídeos concluídos.**\n\n"+'\n'.join(linhas)
    except Exception as e:
        traceback.print_exc()
        raise gr.Error(str(e))


# Interface acessível: duas jornadas claras, linguagem simples e detalhes técnicos opcionais.
CSS = """
/* Prévia do vídeo exportado: tamanho estável, centralizada e responsiva. */
#jw-final-video {width:100% !important;max-width:750px !important;margin:12px auto 20px !important;}
#jw-final-video video {display:block !important;width:100% !important;height:420px !important;max-height:420px !important;object-fit:contain !important;background:#05070b !important;border-radius:10px !important;}
#jw-final-video .video-container {max-height:420px !important;background:#05070b !important;overflow:hidden !important;}
@media(max-width:640px){#jw-final-video video{height:260px !important;max-height:260px !important;}#jw-final-video .video-container{max-height:260px !important;}}

/* Editor de legendas manuais: contraste consistente com Dark Neon (Gradio 5/6). */
#jw-manual-captions {--body-text-color:#f4f7ff;--input-background-fill:#111c2d;--background-fill-primary:#111c2d;--background-fill-secondary:#16243a;--border-color-primary:#34465f;}
#jw-manual-captions table, #jw-manual-captions tbody, #jw-manual-captions tr, #jw-manual-captions td {background:#111c2d !important;color:#f4f7ff !important;}
#jw-manual-captions th, #jw-manual-captions thead, #jw-manual-captions thead tr {background:#1b2a40 !important;color:#fff !important;}
#jw-manual-captions td, #jw-manual-captions th {border-color:#354861 !important;}
#jw-manual-captions input, #jw-manual-captions textarea, #jw-manual-captions [contenteditable=true] {background:#111c2d !important;color:#fff !important;-webkit-text-fill-color:#fff !important;caret-color:#facc15 !important;}
#jw-manual-captions input::placeholder {color:#aab7ca !important;}
#jw-manual-captions td:focus-within, #jw-manual-captions td.selected {background:#223654 !important;}
#jw-add-caption {background:#eab308 !important;color:#101827 !important;border:1px solid #facc15 !important;font-weight:800 !important;}
#jw-remove-caption {border:1px solid #52637a !important;}

:root { --jw-navy:#07172c; --jw-blue:#174b91; --jw-electric:#3988ff; }
.gradio-container {max-width: 1200px !important; margin:auto !important; padding-bottom:12px !important;}
#hero {position:relative;overflow:hidden;padding:34px 38px;border-radius:22px;background:linear-gradient(115deg,#02060d 0%,#081c3b 49%,#164e9a 100%);color:#fff;margin-bottom:18px;box-shadow:0 16px 38px rgba(4,21,49,.22);}

/* Zoom: manter contraste no tema escuro inclusive em foco, hover e seleções. */
#jw-zoom-help code, #jw-zoom-example code {background:#172335 !important;color:#f8fafc !important;border:1px solid #43566f !important;}
.jw-zoom-item {background:#111b29 !important;border:1px solid #3c4e65 !important;border-radius:12px !important;padding:12px !important;margin:8px 0 !important;}
.jw-zoom-item input, .jw-zoom-item input:hover, .jw-zoom-item input:focus,
.jw-zoom-item textarea, .jw-zoom-item textarea:hover, .jw-zoom-item textarea:focus,
.jw-zoom-item [role="combobox"], .jw-zoom-item [role="combobox"]:hover,
.jw-zoom-item .wrap, .jw-zoom-item .wrap:hover {
 background:#172335 !important;color:#f8fafc !important;-webkit-text-fill-color:#f8fafc !important;
}
.jw-zoom-item input::placeholder {color:#aabbd1 !important;opacity:1 !important;}
.jw-zoom-item input:-webkit-autofill {box-shadow:0 0 0 1000px #172335 inset !important;-webkit-text-fill-color:#f8fafc !important;}
.jw-zoom-item label, .jw-zoom-item span {color:#f8fafc !important;}
#hero:after {content:'';position:absolute;right:-60px;top:-110px;width:320px;height:320px;border-radius:50%;background:radial-gradient(circle,rgba(82,153,255,.25),transparent 68%);pointer-events:none;}
#hero h1,#hero p {color:#fff !important;position:relative;z-index:1;}
#hero h1 {font-size:clamp(1.65rem,3vw,2.65rem);font-weight:850;letter-spacing:-.035em;margin:9px 0;line-height:1.13;}
#hero p {max-width:660px;opacity:.86;font-size:1.04rem;line-height:1.6;margin:0;}
#hero .jw-eyebrow {font-size:.76rem;font-weight:800;letter-spacing:.17em;color:#8dc1ff !important;text-transform:uppercase;}
#hero .jw-chip {display:inline-block;margin-top:16px;padding:7px 12px;border:1px solid rgba(170,207,255,.32);border-radius:100px;color:#c5dcff;font-size:.8rem;background:rgba(255,255,255,.07);}
#journey {border:1px solid var(--border-color-primary,#ddd);border-radius:15px;padding:15px 18px;margin-bottom:10px;background:var(--background-fill-secondary,#f8fafc);}
#journey strong {color:var(--body-text-color,#17212f);}
.step-title {font-size:1.08rem;font-weight:700;margin-top:14px;}
.helper {color:var(--body-text-color-subdued);font-size:.94rem;}
#primary-action {margin-top:12px;}
#primary-action,#export-action {border-radius:14px !important;font-size:1.05rem !important;letter-spacing:.01em;min-height:54px !important;}
#export-action {background:linear-gradient(110deg,#067a72,#0caa94) !important;border-color:#068a7e !important;box-shadow:0 8px 20px rgba(6,140,124,.2) !important;}
.gradio-container button {border-radius:11px !important;transition:transform .15s ease,box-shadow .15s ease,filter .15s ease;}
.gradio-container button:hover {transform:translateY(-1px);box-shadow:0 5px 13px rgba(20,50,90,.13);}
.gradio-container button:focus-visible {outline:3px solid #f5ac36 !important;outline-offset:2px;}

.gradio-container button.primary {background:linear-gradient(100deg,#1251a5,#2776dd) !important;border-color:#2469c4 !important;color:white !important;font-weight:750 !important;min-height:46px;box-shadow:0 6px 16px rgba(27,94,184,.17);transition:filter .2s ease,transform .2s ease;}
.gradio-container button.primary:hover {filter:brightness(1.12);transform:translateY(-1px);}
#download-video,#download-batch {border:2px solid #367bd2 !important;border-radius:16px !important;padding:12px !important;background:rgba(35,111,211,.06) !important;}
#download-video button,#download-batch button {font-weight:800 !important;}
.jw-ready {border:1px solid #3d8bd9;border-left:5px solid #2a80d9;background:linear-gradient(105deg,rgba(31,113,213,.11),rgba(31,113,213,.03));border-radius:14px;padding:17px 19px;margin:10px 0;}
.jw-ready h3 {margin:0 0 6px;font-size:1.15rem;}
.jw-ready p {margin:0;line-height:1.5;}
.pv-item {padding:12px 14px;margin:9px 0;border:1px solid var(--border-color-primary,#ccc);border-radius:12px;}
.pv-row {display:flex;justify-content:space-between;gap:12px;margin-bottom:7px;}
.pv-track {background:var(--background-fill-secondary,#ddd);height:10px;border-radius:9px;overflow:hidden;}
.pv-item small {display:block;margin-top:7px;opacity:.85;}
#jw-footer {margin-top:32px;padding:23px 24px;border-radius:17px;background:linear-gradient(120deg,#040b17,#0b2547);color:#d4e3fa;text-align:center;line-height:1.8;}
#jw-footer strong {color:white;font-size:1.05rem;}
#jw-footer small {color:#9fb7d5;}
@media(max-width:640px){#hero{padding:25px 22px;border-radius:16px}#hero h1{font-size:1.8rem}#journey{padding:13px}}

/* v0.9.6: interface compacta, hierarquia e foco na ação principal. */
.gradio-container {max-width:1320px !important;padding:14px 24px 42px !important;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif !important;}
#hero {padding:26px 34px !important;margin-bottom:16px !important;border-radius:20px !important;background:linear-gradient(115deg,#071426 0%,#0d2c58 65%,#1a5092 100%) !important;box-shadow:0 12px 28px rgba(8,25,56,.13) !important;}
#hero h1 {font-size:clamp(1.7rem,3vw,2.35rem) !important;letter-spacing:-.04em !important;margin:7px 0 !important;}
#hero h1 span {color:#a9d1ff !important;}
#hero p {font-size:.97rem !important;line-height:1.5 !important;max-width:720px !important;}
#hero .jw-version {margin-left:10px;padding:3px 9px;border-radius:999px;border:1px solid #79b8ff;color:#d8eaff;font-size:.68rem;letter-spacing:.08em;}
.jw-hero-tags {display:flex;flex-wrap:wrap;gap:8px;margin-top:15px;}
.jw-hero-tags span {font-size:.76rem;padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);color:#e0edff;}
#journey {display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 22px !important;border-radius:14px !important;margin-bottom:18px !important;}
#journey>div {display:grid;grid-template-columns:auto 1fr;column-gap:9px;align-items:center;}
#journey strong {font-size:.85rem;}
#journey small {grid-column:2;color:var(--body-text-color-subdued);font-size:.71rem;}
#journey i {font-size:1.5rem;font-style:normal;color:#8da2b8;}
.jw-step {grid-row:span 2;width:29px;height:29px;display:grid;place-items:center;background:#e7f1ff;border-radius:10px;color:#1456aa;font-weight:800;font-size:.83rem;}
.jw-section-heading {margin-top:20px !important;margin-bottom:7px !important;}
.jw-section-heading h3 {font-size:1.15rem !important;letter-spacing:-.02em;}
.jw-subsection {margin:14px 0 8px !important;}
.jw-settings-grid {align-items:start !important;gap:14px !important;}
.jw-settings-grid>.column {gap:10px !important;}
.jw-settings-grid .accordion {border-radius:13px !important;border:1px solid var(--border-color-primary,#dce4ef) !important;overflow:hidden;}
.jw-settings-grid .accordion button {font-weight:700 !important;}
#primary-action,#export-action,#export-action-batch {min-height:50px !important;font-weight:750 !important;border-radius:12px !important;}
#export-action-batch {background:linear-gradient(110deg,#067a72,#0caa94) !important;border-color:#068a7e !important;}
@media(max-width:760px){.gradio-container{padding:10px 12px 28px !important}#hero{padding:22px !important}#journey{padding:10px !important;gap:4px}#journey small{display:none}#journey>div{display:flex;gap:5px}#journey strong{font-size:.75rem}.jw-step{width:24px;height:24px}}
@media(prefers-reduced-motion:reduce){.gradio-container button{transition:none !important}.gradio-container button:hover{transform:none !important}}


/* v0.9.8 — Dark Neon: cores e contraste coerentes em Gradio 5 e 6. */
:root, body, .gradio-container {
  --background-fill-primary:#080b10 !important;
  --background-fill-secondary:#121924 !important;
  --block-background-fill:#131a25 !important;
  --input-background-fill:#0d131d !important;
  --body-background-fill:#080b10 !important;
  --body-text-color:#f5f7fb !important;
  --body-text-color-subdued:#b3bfd1 !important;
  --block-label-text-color:#facc15 !important;
  --block-title-text-color:#f5f7fb !important;
  --border-color-primary:#344052 !important;
  --color-accent:#facc15 !important;
  --button-primary-background-fill:#facc15 !important;
  --button-primary-background-fill-hover:#fde047 !important;
  --button-primary-text-color:#111827 !important;
  color-scheme:dark !important;
}
html,body,body > gradio-app {background:#080b10 !important;color:#f5f7fb !important;}
.gradio-container {background:#080b10 !important;color:#f5f7fb !important;max-width:1320px !important;}
.gradio-container .block, .gradio-container .form, .gradio-container .panel,
.gradio-container .accordion, .gradio-container .tabs, .gradio-container .tabitem {
  color:#f5f7fb !important;
}
.gradio-container input,.gradio-container textarea,.gradio-container select {background:#0d131d !important;color:#fff !important;border-color:#3a4658 !important;}
.gradio-container label,.gradio-container p,.gradio-container span,.gradio-container .prose {color:inherit;}
.gradio-container .prose p,.gradio-container .prose li {color:#d5deeb !important;}
.gradio-container button.primary,#export-action,#export-action-batch,#primary-action {
  background:#facc15 !important;border:1px solid #facc15 !important;color:#111827 !important;
  box-shadow:0 6px 20px rgba(250,204,21,.13) !important;font-weight:850 !important;
}
.gradio-container button.primary:hover,#export-action:hover,#export-action-batch:hover {background:#fde047 !important;filter:none !important;}
.gradio-container button:focus-visible,.gradio-container a:focus-visible {outline:3px solid #facc15 !important;outline-offset:3px;}
#hero {background:linear-gradient(115deg,#0c111a,#111d30 60%,#243b60) !important;border:1px solid #2e3a4d;box-shadow:0 14px 34px rgba(0,0,0,.35) !important;}
#hero h1 span,#hero .jw-eyebrow {color:#facc15 !important;}
#hero .jw-version {border-color:#facc15 !important;color:#facc15 !important;}
#hero .jw-hero-tags span {background:#1a2534 !important;color:#f2f5fa !important;border-color:#3b475a !important;}
#journey {background:#131a25 !important;border-color:#354052 !important;}
#journey strong {color:#fff !important;}
#journey small {color:#b4bfd0 !important;}
.jw-step {background:#facc15 !important;color:#111827 !important;}
.jw-section-heading {margin-top:32px !important;margin-bottom:16px !important;}
.jw-section-heading h3 {font-size:clamp(1.45rem,2.4vw,1.9rem) !important;line-height:1.3 !important;font-weight:850 !important;color:#facc15 !important;letter-spacing:-.025em;}
.jw-subsection {margin:24px 0 14px !important;}
.jw-subsection p,.jw-subsection strong {font-size:clamp(1.18rem,2vw,1.5rem) !important;line-height:1.5 !important;color:#facc15 !important;font-weight:850 !important;}
.jw-settings-grid .accordion {background:#151d29 !important;border-color:#354052 !important;}
.jw-settings-grid .accordion button {color:#f5f7fb !important;}
#download-video,#download-batch {border:2px solid #facc15 !important;background:#242311 !important;border-radius:16px !important;padding:18px !important;box-shadow:0 0 0 3px rgba(250,204,21,.07) !important;}
#download-video button,#download-batch button {background:#facc15 !important;color:#111827 !important;font-weight:850 !important;border-radius:10px !important;min-height:46px !important;}
#download-video a,#download-batch a {color:#facc15 !important;font-weight:800 !important;text-decoration:underline !important;text-underline-offset:3px;}
.jw-ready {background:#16261d !important;border-color:#4ade80 !important;border-left:5px solid #4ade80 !important;color:#fff !important;}
.jw-ready h3 {color:#86efac !important;font-size:1.45rem !important;}
.jw-ready p {color:#e4f4e9 !important;}
#jw-footer {background:#101724 !important;border:1px solid #2c3648 !important;}
#jw-footer,#jw-footer div {color:#dce5f2 !important;}
#jw-footer small {color:#b4c4d9 !important;}
.pv-item {background:#151d29 !important;border-color:#354052 !important;}
.pv-track {background:#303b4c !important;}
@media(max-width:760px){
  .gradio-container {padding:10px 12px 28px !important;}
  #hero {padding:22px !important;}
  #journey {flex-wrap:wrap !important;justify-content:center !important;}
  .jw-section-heading h3 {font-size:1.45rem !important;}
  .jw-settings-grid {flex-direction:column !important;}
  .jw-settings-grid > .column {min-width:0 !important;width:100% !important;}
}
/* v0.9.8.1 — correção de contraste: componentes nativos do Gradio.
   Limita as regras à aplicação; mantém botões amarelos e estados acessíveis. */
.gradio-container {
  --block-background-fill:#131a25 !important;
  --block-border-color:#344052 !important;
  --input-background-fill:#0d131d !important;
  --input-border-color:#435167 !important;
  --input-text-color:#f5f7fb !important;
  --body-text-color:#f5f7fb !important;
  --body-text-color-subdued:#b8c6d9 !important;
  --button-secondary-background-fill:#222c3b !important;
  --button-secondary-background-fill-hover:#344256 !important;
  --button-secondary-text-color:#f5f7fb !important;
  --button-secondary-border-color:#52627a !important;
  --button-secondary-border-color-hover:#facc15 !important;
  --checkbox-background-color:#0d131d !important;
  --checkbox-border-color:#70829c !important;
  --radio-circle:#facc15 !important;
  --table-even-background-fill:#131a25 !important;
  --table-odd-background-fill:#192333 !important;
}
/* Cartões e linhas de uploads — elimina fundo quase branco com texto branco. */
.gradio-container .file-preview,
.gradio-container .file-preview .file,
.gradio-container .file-preview .file-container,
.gradio-container .file-preview .file-item,
.gradio-container .file-preview .file-name,
.gradio-container .file-preview .file-size,
.gradio-container .file-preview .file-list,
.gradio-container .file-preview .file-list > *,
.gradio-container .file-preview li,
.gradio-container .file-preview [class*="file-row"],
.gradio-container .file-preview [class*="file-item"] {
  background:#192333 !important;color:#f5f7fb !important;
  border-color:#3b4a60 !important;
}
.gradio-container .file-preview :is(span,p,div,button,a) {color:#f5f7fb !important;}
.gradio-container .file-preview :is(button,a):hover {color:#facc15 !important;}
/* Radio / checkbox: texto legível em opções ativas e inativas. */
.gradio-container .wrap:has(input[type="radio"]) label,
.gradio-container label:has(input[type="radio"]),
.gradio-container label:has(input[type="checkbox"]) {
  background:#202a39 !important;color:#f5f7fb !important;
  border:1px solid #435167 !important;
}
.gradio-container label:has(input[type="radio"]) span,
.gradio-container label:has(input[type="checkbox"]) span {color:#f5f7fb !important;}
.gradio-container label:has(input[type="radio"]:checked) {
  background:#453b16 !important;border-color:#facc15 !important;
}
.gradio-container input[type="radio"],.gradio-container input[type="checkbox"] {
  accent-color:#facc15 !important;
}
/* Botões secundários não devem herdar texto branco sobre superfície clara. */
.gradio-container button.secondary,
.gradio-container button[aria-pressed],
.gradio-container .file-preview button {
  background:#222c3b !important;color:#f5f7fb !important;
  border-color:#52627a !important;
}
.gradio-container button.secondary:hover,
.gradio-container button[aria-pressed]:hover {background:#344256 !important;}
.gradio-container button:disabled {opacity:.65 !important;cursor:not-allowed !important;}
.gradio-container :is(input,textarea,select)::placeholder {color:#a8b8cc !important;opacity:1 !important;}
.gradio-container :is(input,textarea,select):focus-visible {outline:2px solid #facc15 !important;outline-offset:1px;}
/* Seletores e menus, incluindo listas de opções. */
.gradio-container [role="listbox"],.gradio-container [role="option"],
.gradio-container [role="menu"],.gradio-container [role="menuitem"],
.gradio-container [data-state="open"] [role="option"] {
  background:#182231 !important;color:#f5f7fb !important;
}
.gradio-container [role="option"][aria-selected="true"],
.gradio-container [role="option"]:hover {background:#35445a !important;color:#fff !important;}
/* Indicadores e mensagens de erro/sucesso mantêm distinção. */
.gradio-container .error {color:#fecaca !important;}
.gradio-container .success {color:#bbf7d0 !important;}

/* v0.9.8.2 — indicadores explícitos de seleção, sem depender do desenho nativo
   do radio/checkbox (que varia entre versões do Gradio e navegadores). */
.gradio-container label:has(input[type="radio"]),
.gradio-container label:has(input[type="checkbox"]) {
  position:relative !important;
  cursor:pointer;
}
/* O selo à direita permanece legível mesmo quando o círculo nativo é escuro. */
.gradio-container label:has(input[type="radio"]:checked)::after,
.gradio-container label:has(input[type="checkbox"]:checked)::after {
  content:"✓" !important;
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  width:20px !important;
  height:20px !important;
  min-width:20px !important;
  margin-inline-start:9px !important;
  border-radius:50% !important;
  background:#facc15 !important;
  color:#10151e !important;
  font-size:14px !important;
  line-height:1 !important;
  font-weight:900 !important;
  box-shadow:0 0 0 1px #facc15 !important;
}
.gradio-container label:has(input[type="checkbox"]:checked),
.gradio-container label:has(input[type="radio"]:checked) {
  background:#403714 !important;
  border-color:#facc15 !important;
  color:#fff !important;
}
.gradio-container label:has(input[type="checkbox"]:checked) span,
.gradio-container label:has(input[type="radio"]:checked) span {
  color:#fff !important;
}
.gradio-container label:has(input[type="radio"]:focus-visible),
.gradio-container label:has(input[type="checkbox"]:focus-visible) {
  outline:3px solid #facc15 !important;
  outline-offset:3px !important;
}
.gradio-container label:has(input[type="radio"]:disabled),
.gradio-container label:has(input[type="checkbox"]:disabled) {
  opacity:.6 !important;
  cursor:not-allowed !important;
}


/* Social Manager JW — acabamento visual, sem alterar o fluxo de publicação. */
#ig-result {background:#14251d !important;border:1px solid #35674d !important;border-left:5px solid #4ade80 !important;border-radius:12px !important;padding:14px 17px !important;margin:10px 0 !important;}
#ig-result, #ig-result p, #ig-result span, #ig-result strong {color:#e7f8ed !important;}
#ig-result code, #ig-result .prose code, #ig-result p code {background:#0c1820 !important;color:#f8fafc !important;border:1px solid #50647a !important;border-radius:6px !important;padding:4px 8px !important;font-family:ui-monospace,SFMono-Regular,Consolas,monospace !important;font-weight:750 !important;overflow-wrap:anywhere !important;white-space:normal !important;}
#ig-prepare-btn, #ig-publish-btn, #ig-check-btn {min-height:58px !important;border-radius:13px !important;font-size:1.04rem !important;font-weight:850 !important;letter-spacing:.01em !important;box-shadow:0 7px 18px rgba(0,0,0,.26) !important;transition:transform .15s ease,filter .15s ease,box-shadow .15s ease !important;}
#ig-prepare-btn {background:#2563eb !important;border:2px solid #60a5fa !important;color:#fff !important;}
#ig-prepare-btn:hover:not(:disabled) {background:#1d4ed8 !important;box-shadow:0 9px 23px rgba(37,99,235,.3) !important;}
#ig-publish-btn {background:#facc15 !important;border:2px solid #fde047 !important;color:#111827 !important;}
#ig-publish-btn:hover:not(:disabled) {background:#fde047 !important;box-shadow:0 9px 23px rgba(250,204,21,.26) !important;}
#ig-check-btn {background:#26374d !important;border:2px solid #7591b3 !important;color:#fff !important;}
#ig-check-btn:hover:not(:disabled) {background:#354a65 !important;box-shadow:0 9px 23px rgba(96,165,250,.17) !important;}
#ig-prepare-btn:disabled, #ig-publish-btn:disabled, #ig-check-btn:disabled {opacity:.57 !important;cursor:not-allowed !important;box-shadow:none !important;transform:none !important;}
#ig-prepare-btn:focus-visible, #ig-publish-btn:focus-visible, #ig-check-btn:focus-visible {outline:3px solid #fff !important;outline-offset:3px !important;}
@media(max-width:640px){#ig-prepare-btn,#ig-publish-btn,#ig-check-btn{min-height:54px !important;font-size:.96rem !important;}}

@media(prefers-reduced-motion:reduce){.gradio-container *{scroll-behavior:auto !important;}}

/* Ajuste UX: exemplos inline e edição/hover na grade de legendas. */
#jw-caption-help :is(code,.prose code),#jw-caption-example :is(code,.prose code) {
 background:#1c2a3e !important;color:#f8fafc !important;-webkit-text-fill-color:#f8fafc !important;
 border:1px solid #4b607d !important;border-radius:5px !important;padding:2px 6px !important;
}
#jw-manual-captions :is(td,td:hover,td:focus,td:focus-within,td.selected,td.highlighted,td.editing,td[aria-selected="true"]) {
 background:#152238 !important;color:#f8fafc !important;-webkit-text-fill-color:#f8fafc !important;
}
#jw-manual-captions :is(input,textarea,[contenteditable="true"],[role="textbox"],.cell-input,.edit-cell) {
 background:#152238 !important;color:#f8fafc !important;-webkit-text-fill-color:#f8fafc !important;
 caret-color:#facc15 !important;color-scheme:dark !important;
}
#jw-manual-captions :is(input,textarea,[contenteditable="true"],[role="textbox"]):is(:hover,:focus,:focus-visible,:active) {
 background:#20324e !important;color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;
}
#jw-manual-captions :is(input,textarea)::selection {background:#eab308 !important;color:#111827 !important;}
#jw-manual-captions :is(td,td *)::selection {background:#eab308 !important;color:#111827 !important;}

/* UX: títulos e descrições dos recursos de legendas e zoom. */
.jw-feature-intro {margin:20px 0 11px !important;padding:15px 17px !important;background:#141c28 !important;border:1px solid #344256 !important;border-left:4px solid #facc15 !important;border-radius:12px !important;}
.jw-feature-intro h3 {margin:0 0 7px !important;color:#facc15 !important;font-size:1.22rem !important;font-weight:850 !important;line-height:1.3 !important;}
.jw-feature-intro p {margin:0 !important;color:#d3deed !important;font-size:.92rem !important;line-height:1.55 !important;}
#jw-zoom-section {margin-top:18px !important;border:1px solid #44536b !important;border-radius:12px !important;background:#141c28 !important;overflow:hidden !important;}
#jw-zoom-section > button, #jw-zoom-section > .label-wrap, #jw-zoom-section > .label-wrap > button {color:#facc15 !important;font-weight:850 !important;font-size:1.16rem !important;}
#jw-zoom-section > button:hover, #jw-zoom-section > .label-wrap:hover {background:#1d2a3b !important;}
@media(max-width:640px){.jw-feature-intro{padding:12px 13px !important}.jw-feature-intro h3{font-size:1.1rem !important}}
"""

EXEMPLOS = {
    'Limpar áudio': 'Reduza o chiado e melhore o áudio do vídeo.',
    'Remover pausas': 'Remova silêncios maiores que 2 segundos e melhore o áudio.',
    'Ajustar duração': 'Deixe o vídeo com aproximadamente 5 minutos, sem acelerar a fala.',
    'Edição completa': 'Remova silêncios maiores que 2 segundos, melhore o áudio e deixe o vídeo com aproximadamente 5 minutos.',
}

def preencher_exemplo(escolha):
    return EXEMPLOS.get(escolha, '')

def limpar_analise():
    # Qualquer mudança de entrada/instrução invalida a proposta anterior.
    return '', gr.update(value='', visible=False), gr.update(value='[]', visible=False), gr.update(value='', visible=False), gr.update(visible=False)

def analisar_guiado(video, instrucao):
    ident, resumo, cortes, transcricao = interface_analisar(video, instrucao)
    return ident, gr.update(value=resumo, visible=True), gr.update(value=cortes, visible=True), gr.update(value=transcricao, visible=bool(transcricao)), gr.update(visible=True)

def concluir_guiado(ident, cortes, leg, estilo):
    video, arquivo, srt, mensagem = interface_aplicar(ident, cortes, leg, estilo)
    return gr.update(value=video, visible=True), gr.update(value=arquivo, visible=True), gr.update(value=srt, visible=bool(srt)), gr.update(value='✅ ' + mensagem, visible=True)

def concluir_lote(arquivos, instrucao, leg, estilo, progress=gr.Progress()):
    pacote, relatorio = interface_lote(arquivos, instrucao, leg, estilo, progress)
    return gr.update(value=pacote, visible=True), gr.update(value=relatorio, visible=True)


# Atualização contínua de indicadores enquanto o processamento roda em thread.
def _executar_com_eventos(trabalho):
    eventos=queue.Queue()
    def notificar(*dados): eventos.put(('progresso',dados))
    def rodar():
        try: eventos.put(('resultado',trabalho(notificar)))
        except Exception as e: eventos.put(('erro',e))
    threading.Thread(target=rodar,daemon=True).start()
    while True:
        try: tipo,valor=eventos.get(timeout=.35)
        except queue.Empty:
            yield ('aguardando',None)
            continue
        yield (tipo,valor)
        if tipo in ('resultado','erro'): break

def _barra(nome, fracao, etapa, estado='processando'):
    pct=round(100*max(0.,min(1.,fracao)))
    cor='#16866d' if estado=='concluido' else '#ba4141' if estado=='erro' else '#327ac2'
    titulo=html.escape(str(nome)); descricao=html.escape(str(etapa))
    return (f'<section class="pv-item"><div class="pv-row"><strong>{titulo}</strong>'
            f'<span>{pct}%</span></div><div class="pv-track" role="progressbar" aria-valuemin="0" '
            f'aria-valuemax="100" aria-valuenow="{pct}" aria-label="{titulo}">'
            f'<div style="width:{pct}%;background:{cor};height:100%;border-radius:9px"></div></div>'
            f'<small>{descricao}</small></section>')

def aplicar_com_progresso(ident,cortes,leg,estilo,visual,tamanho,posicao,transicao,duracao_transicao,trilha,arquivo_musica,volume_musica,manter_audio,fade_musica,filtro_video,intensidade_filtro,brilho_filtro,contraste_filtro,cortes_manuais,modo_legendas,legendas_manuais,*extras):
    ensure_valid()
    if not ident: raise gr.Error('Analise o vídeo antes de confirmar a edição.')
    zoom_valores = extras[:60]
    efeitos_valores = extras[60:]
    eventos_efeitos = [list(efeitos_valores[i+1:i+4]) for i in range(0,len(efeitos_valores),4) if efeitos_valores[i]]
    # Cada linha possui: ativo, posição, início, fim e intensidade.
    # Os controles inativos não são enviados ao FFmpeg.
    intervalos_zoom = [list(zoom_valores[i+1:i+5]) for i in range(0, len(zoom_valores), 5) if zoom_valores[i]]
    usar_zoom = bool(intervalos_zoom)
    usar_legendas = (modo_legendas == 'Manuais') or (modo_legendas == 'Automáticas' and leg)
    def trabalho(cb):
        caminho=aplicar_proposta(ident,cortes,callback=lambda p,s:cb((.72 if usar_legendas else 1)*p,s),transicao=transicao,duracao_transicao=duracao_transicao,cortes_manuais=cortes_manuais)
        if usar_zoom:
            caminho=aplicar_zoom(caminho,intervalos_zoom,callback=lambda msg:cb(.74,msg))
        srt=None
        if modo_legendas == 'Manuais':
            caminho,srt=legendar_manual(caminho,legendas_manuais,callback=lambda p,s:cb(.72+.28*p,s),visual=visual,tamanho=tamanho,posicao=posicao)
        elif modo_legendas == 'Automáticas' and leg:
            caminho,srt=legendar_video(caminho,estilo,callback=lambda p,s:cb(.72+.28*p,s),visual=visual,tamanho=tamanho,posicao=posicao)
        caminho=adicionar_musica(caminho,trilha,arquivo_musica,volume_musica,manter_audio,fade_musica,callback=lambda msg:cb(.98,msg))
        if eventos_efeitos:
            caminho=aplicar_efeitos(caminho,eventos_efeitos,callback=lambda msg:cb(.985,msg))
        caminho=aplicar_filtro_video(caminho,filtro_video,intensidade_filtro,brilho_filtro,contraste_filtro,callback=lambda msg:cb(.99,msg))
        return caminho,srt
    for tipo,dados in _executar_com_eventos(trabalho):
        if tipo=='progresso':
            pct,etapa=dados
            yield _barra('Seu vídeo',pct,etapa),gr.update(),gr.update(),gr.update(),gr.update(),gr.update(visible=False),gr.update(visible=False)
        elif tipo=='resultado':
            caminho,srt=dados
            yield _barra('Seu vídeo',1,'Concluído','concluido'),gr.update(value=caminho,visible=True),gr.update(value=caminho,visible=True),gr.update(value=srt,visible=bool(srt)),gr.update(value='✅ Vídeo pronto! Use a área de download destacada abaixo.',visible=True),gr.update(visible=True),gr.update(visible=True)
        elif tipo=='erro':
            yield _barra('Seu vídeo',1,'Falha na edição','erro'),gr.update(),gr.update(),gr.update(),gr.update(value='❌ '+html.escape(str(dados)),visible=True),gr.update(visible=False),gr.update(visible=False)

def lote_com_progresso(arquivos,instrucao,leg,estilo,visual,tamanho,posicao,transicao,duracao_transicao,trilha,arquivo_musica,volume_musica,manter_audio,fade_musica,filtro_video,intensidade_filtro,brilho_filtro,contraste_filtro):
    ensure_valid()
    nomes=[Path(a).name for a in (arquivos or [])]
    if not nomes: raise gr.Error('Selecione ao menos um vídeo MP4 ou MOV.')
    estados=[(0.,'Aguardando','aguardando') for _ in nomes]
    def painel():
        feitos=sum(x[2] in ('concluido','erro') for x in estados)
        geral=round(100*sum(x[0] for x in estados)/len(estados))
        return (f'<p><strong>Progresso geral: {geral}% · {feitos}/{len(estados)} finalizados</strong></p>'+
                ''.join(_barra(nome,*estado) for nome,estado in zip(nomes,estados)))
    def trabalho(cb):
        return executar_lote(arquivos,instrucao,leg,estilo,status_callback=lambda *args:cb(*args),visual=visual,tamanho=tamanho,posicao=posicao,transicao=transicao,duracao_transicao=duracao_transicao,trilha=trilha,arquivo_musica=arquivo_musica,volume_musica=volume_musica,manter_audio=manter_audio,fade_musica=fade_musica,filtro_video=filtro_video,intensidade_filtro=intensidade_filtro,brilho_filtro=brilho_filtro,contraste_filtro=contraste_filtro)
    yield painel(),gr.update(),gr.update(),gr.update(visible=False)
    for tipo,dados in _executar_com_eventos(trabalho):
        if tipo=='progresso':
            i,p,etapa,status=dados
            estados[i]=(p,etapa,status)
            yield painel(),gr.update(),gr.update(),gr.update(visible=False)
        elif tipo=='resultado':
            pacote,registros=dados
            ok=sum(r['status']=='concluido' for r in registros)
            linhas=[f"- **{r['arquivo']}**: "+('Concluído' if r['status']=='concluido' else 'Erro — '+str(r['erro'])) for r in registros]
            yield painel(),gr.update(value=pacote,visible=True),gr.update(value=f'**{ok}/{len(registros)} vídeos concluídos.**\n\n'+'\n'.join(linhas),visible=True),gr.update(visible=True)
        elif tipo=='erro':
            yield painel(),gr.update(),gr.update(value='❌ '+html.escape(str(dados)),visible=True),gr.update(visible=False)

# Gradio 6 recebe CSS/tema em launch; Gradio 5 recebe em Blocks.
_GRADIO6 = int(gr.__version__.split('.')[0]) >= 6
_blocks_style = {} if _GRADIO6 else {'css': CSS, 'theme': gr.themes.Base(primary_hue=gr.themes.colors.yellow, neutral_hue=gr.themes.colors.slate)}
with gr.Blocks(title='EditAI Videos JW — Editor inteligente de vídeos', **_blocks_style) as app:
    gr.HTML('<header id="hero"><div class="jw-eyebrow">✦ ESTÚDIO INTELIGENTE <span class="jw-version">BETA 0.9.8.4</span></div><h1>EditAI <span>Videos JW</span></h1><p>Da ideia ao vídeo pronto. Importe seus arquivos, descreva a edição e personalize o resultado em poucos passos.</p><div class="jw-hero-tags"><span>⚡ Edição automática</span><span>🎵 Música</span><span>🎨 Filtros</span><span>✨ Transições</span></div></header>')
    gr.HTML('<nav id="journey" aria-label="Etapas da edição"><div><span class="jw-step">1</span><strong>Importar</strong><small>Selecione seus vídeos</small></div><i>›</i><div><span class="jw-step">2</span><strong>Personalizar</strong><small>Descreva e ajuste</small></div><i>›</i><div><span class="jw-step">3</span><strong>Exportar</strong><small>Revise e baixe</small></div></nav>')
    with gr.Tabs():
        with gr.Tab('🎞️ Um vídeo'):
            gr.Markdown('### ① Importe seu vídeo',elem_classes=['jw-section-heading'])
            gr.Markdown('Envie um arquivo MP4 ou MOV. Você poderá conferir os cortes sugeridos antes de editar. A exportação será em MP4.', elem_classes=['helper'])
            with gr.Row(equal_height=False):
                with gr.Column(scale=6):
                    video=gr.File(label='Seu vídeo (MP4 ou MOV)',file_types=['.mp4','.mov'],type='filepath')
                with gr.Column(scale=5):
                    gr.Markdown('### ② Descreva a edição',elem_classes=['jw-section-heading'])
                    prompt=gr.Textbox(label='Seu pedido de edição',lines=4,placeholder='Ex.: Tire as pausas longas, melhore minha voz e deixe o vídeo com aproximadamente 5 minutos.')
                    exemplo=gr.Dropdown(choices=list(EXEMPLOS),label='Ou escolha uma sugestão pronta',value=None,interactive=True)
                    exemplo.change(preencher_exemplo,exemplo,prompt)
                    gr.HTML('<section class="jw-feature-intro"><h3>▣ Legendas do vídeo</h3><p>Escolha como as legendas serão criadas: sem legendas, geradas automaticamente a partir das falas ou escritas por você com horários personalizados.</p></section>')
                    modo_legendas=gr.Radio(choices=['Sem legendas','Automáticas','Manuais'],value='Sem legendas',label='Tipo de legendas')
                    with gr.Column(visible=False) as painel_manuais:
                        gr.Markdown('**Digite o texto e os horários de cada legenda.** Use `MM:SS` (ex.: `00:01` até `00:32`) ou `MM:SS.mmm` para milissegundos. Os horários correspondem ao **vídeo final, após os cortes**. As legendas aparecem no MP4 e também são exportadas em SRT.', elem_id='jw-caption-help')
                        legendas_manuais=gr.Dataframe(headers=['Texto da legenda','Início (MM:SS)','Fim (MM:SS)'],datatype=['str','str','str'],value=[['Bem-vindos ao vídeo!','00:00','00:03']],row_count=(1,'dynamic'),col_count=(3,'fixed'),type='array',label='Legendas personalizadas',interactive=True,elem_id='jw-manual-captions')
                        with gr.Row():
                            adicionar_legenda=gr.Button('＋ Adicionar legenda',variant='primary',elem_id='jw-add-caption')
                            remover_legenda=gr.Button('− Remover última legenda',variant='secondary',elem_id='jw-remove-caption')
                        gr.Markdown('**Exemplo:** `Olá, pessoal!` | `00:01` | `00:04`  ·  Para apagar uma legenda específica, limpe sua linha ou use o menu da tabela.',elem_classes=['helper'],elem_id='jw-caption-example')
                        def _adicionar_linha_legenda(linhas):
                            if hasattr(linhas,'values'): linhas=linhas.values.tolist()
                            linhas=[list(l) for l in (linhas or [])]
                            linhas.append(['','00:00','00:03'])
                            return linhas
                        def _remover_linha_legenda(linhas):
                            if hasattr(linhas,'values'): linhas=linhas.values.tolist()
                            linhas=[list(l) for l in (linhas or [])]
                            return linhas[:-1] if len(linhas)>1 else [['','00:00','00:03']]
                        adicionar_legenda.click(_adicionar_linha_legenda,inputs=legendas_manuais,outputs=legendas_manuais,queue=False)
                        remover_legenda.click(_remover_linha_legenda,inputs=legendas_manuais,outputs=legendas_manuais,queue=False)
                    gr.HTML('<section class="jw-feature-intro"><h3>✦ Legendas automáticas</h3><p>O EditAI transcreve as falas e sincroniza as legendas. Selecione <strong>Automáticas</strong> acima para ativar e personalizar o estilo.</p></section>')
                    ativar_legendas=gr.Checkbox(label='Adicionar legendas ao vídeo final',value=False)
                    estilo=gr.Radio(choices=['Tradicional','Dinâmica'],value='Tradicional',label='Como mostrar as legendas',visible=False)
                    with gr.Column(visible=False) as aparencia:
                        visual=gr.Dropdown(choices=list(ESTILOS_VISUAIS),value='Clássica',label='Estilo visual das legendas')
                        tamanho=gr.Slider(minimum=60,maximum=160,step=10,value=100,label='Tamanho da legenda (%)')
                        posicao=gr.Radio(choices=['Inferior','Centro','Superior'],value='Inferior',label='Posição da legenda')
                        gr.Markdown('**Dica:** “Palavra destacada” combina com o modo Dinâmica. As escolhas são aplicadas ao MP4 exportado.')
                    # Registre os eventos somente depois de criar todos os componentes.
                    # As legendas manuais utilizam as opcoes visuais, sem exigir a caixa de legendas automaticas.
                    modo_legendas.change(
                        lambda m: (
                            gr.update(visible=m == 'Manuais'),
                            gr.update(value=m == 'Automáticas', visible=m == 'Automáticas'),
                            gr.update(visible=m == 'Automáticas'),
                            gr.update(visible=m in ('Manuais', 'Automáticas')),
                        ),
                        inputs=modo_legendas,
                        outputs=[painel_manuais, ativar_legendas, estilo, aparencia],
                    )
                    ativar_legendas.change(
                        lambda x: gr.update(visible=bool(x)),
                        inputs=ativar_legendas,
                        outputs=estilo,
                    )
                    gr.HTML('<section class="jw-feature-intro"><h3>🔎 Zoom programável</h3><p>Aproxime suavemente partes do vídeo para destacar detalhes. Defina a posição, a intensidade e os horários; abra a seção abaixo para configurar os zooms.</p></section>')
                    with gr.Accordion('🔎 Zoom programável · Opcional', open=False, elem_id='jw-zoom-section'):
                        gr.Markdown('**Destaque momentos importantes com uma aproximação suave.** Escolha esquerda, centro ou direita, a intensidade e o intervalo de cada zoom. Use `MM:SS` (ex.: `00:01` até `00:32`) ou `MM:SS.mmm`. Os horários se referem ao vídeo final, após os cortes, e não podem se sobrepor.', elem_id='jw-zoom-help')
                        gr.Markdown('**Intervalos de zoom**')
                        zoom_controles = []
                        zoom_grupos = []
                        MAX_ZOOMS = 12
                        for indice_zoom in range(MAX_ZOOMS):
                            with gr.Group(visible=(indice_zoom == 0), elem_classes=['jw-zoom-item']) as grupo_zoom:
                                gr.Markdown(f'**Zoom {indice_zoom + 1}**')
                                with gr.Row():
                                    zoom_pos = gr.Dropdown(choices=['Esquerda','Centro','Direita'], value='Centro', label='Posição', interactive=True, elem_classes=['jw-zoom-select'])
                                    zoom_inicio = gr.Textbox(value='00:01', label='Início (MM:SS)', placeholder='00:01', interactive=True)
                                    zoom_fim = gr.Textbox(value='00:04', label='Fim (MM:SS)', placeholder='00:04', interactive=True)
                                    zoom_intensidade = gr.Dropdown(choices=['1.2x','1.5x','2.0x'], value='1.5x', label='Intensidade', interactive=True, elem_classes=['jw-zoom-select'])
                                zoom_ativo = gr.State(indice_zoom == 0)
                                zoom_controles.extend([zoom_ativo, zoom_pos, zoom_inicio, zoom_fim, zoom_intensidade])
                                zoom_grupos.append(grupo_zoom)
                        zoom_quantidade = gr.State(1)
                        with gr.Row():
                            adicionar_zoom = gr.Button('＋ Adicionar zoom', variant='primary')
                            remover_zoom = gr.Button('− Remover último zoom', variant='secondary')
                        def _alterar_quantidade_zooms(qtd, incremento):
                            novo = max(1, min(MAX_ZOOMS, int(qtd) + incremento))
                            return [novo] + [gr.update(visible=(i < novo)) for i in range(MAX_ZOOMS)] + [i < novo for i in range(MAX_ZOOMS)]
                        saidas_zoom = [zoom_quantidade] + zoom_grupos + zoom_controles[::5]
                        adicionar_zoom.click(lambda n: _alterar_quantidade_zooms(n, 1), inputs=zoom_quantidade, outputs=saidas_zoom, queue=False)
                        remover_zoom.click(lambda n: _alterar_quantidade_zooms(n, -1), inputs=zoom_quantidade, outputs=saidas_zoom, queue=False)
                        gr.Markdown('**Exemplo:** posição **Esquerda**, início **00:03**, fim **00:08**, intensidade **1.2x**. Máximo de 12 intervalos.', elem_id='jw-zoom-example')
                    analisar=gr.Button('🔍 Analisar meu vídeo',variant='primary',elem_id='primary-action')
            identificador=gr.State('')
            gr.Markdown('### ③ Personalize e exporte',elem_classes=['jw-section-heading'])
            gr.Markdown('Analise primeiro. Depois, escolha os acabamentos abaixo e exporte quando estiver satisfeito.',elem_classes=['helper'])
            resumo=gr.Markdown(visible=False)
            with gr.Accordion('Detalhes avançados — revisar cortes e transcrição',open=False):
                gr.Markdown('**Opcional:** ajuste os cortes em segundos. Use uma lista JSON válida; cada corte precisa de `inicio` e `fim`.')
                cortes=gr.Code(label='Cortes sugeridos (JSON)',language='json',lines=12,value='[]',visible=False)
                transcricao=gr.Textbox(label='Transcrição para conferência',lines=9,interactive=False,visible=False)
            with gr.Accordion('✂️ Remover trechos manualmente · Opcional',open=False):
                gr.Markdown('Assista ao vídeo original e informe os intervalos que deseja **excluir**. Um intervalo por linha, no formato `MM:SS - MM:SS` ou `HH:MM:SS - HH:MM:SS`. Os tempos se referem ao **vídeo original**, antes dos cortes automáticos. Intervalos sobrepostos serão unidos. O arquivo original não será alterado.')
                preview_cortes=gr.Video(label='Pré-visualização do vídeo original',interactive=False)
                cortes_manuais=gr.Textbox(label='Intervalos a remover (um por linha)',lines=4,placeholder='02:30 - 03:15\n05:10 - 05:25')
                gr.Markdown('**Exemplo:** `02:30 - 03:15` remove 45 segundos. Deixe vazio para não aplicar cortes manuais. Os cortes serão combinados com os sugeridos automaticamente.')
                video.change(lambda arquivo: arquivo,inputs=video,outputs=preview_cortes)
            gr.Markdown('**Acabamento do vídeo**  ·  Escolha apenas os recursos que quiser usar.',elem_classes=['jw-subsection'])
            with gr.Row(equal_height=False, elem_classes=['jw-settings-grid']):
                with gr.Column(scale=1, min_width=300):
                    with gr.Accordion('✨ Transições · Opcional',open=False):
                        gr.Markdown('Escolha como os trechos preservados serão unidos. O efeito é aplicado em todas as junções; com apenas um trecho, não há transição.')
                        transicao=gr.Radio(choices=['Nenhuma','Dissolver','Fade para preto','Deslizar'],value='Nenhuma',label='Efeito de transição')
                        duracao_transicao=gr.Slider(minimum=0.2,maximum=2.0,step=0.1,value=0.7,label='Duração da transição (segundos)')
                    with gr.Accordion('🎵 Música de fundo · Opcional',open=False):
                        gr.Markdown('Trilhas instrumentais originais incluídas no aplicativo, ou importe sua própria música. A trilha é aplicada ao vídeo exportado.')
                        trilha=gr.Dropdown(choices=list(TRACKS),value='Sem música',label='🎼 Escolha uma música')
                        with gr.Row():
                            musica_preview=gr.Audio(label='▶️ Ouvir a trilha selecionada',interactive=False)
                            arquivo_musica=gr.File(label='📁 Importar música própria (MP3/WAV/M4A...)',file_types=['.mp3','.wav','.m4a','.aac','.flac','.ogg'],type='filepath')
                        volume_musica=gr.Slider(minimum=0,maximum=100,step=5,value=20,label='🔊 Volume da música (%)')
                        manter_audio=gr.Checkbox(value=True,label='🎙️ Manter o áudio original do vídeo')
                        fade_musica=gr.Checkbox(value=True,label='🌅 Fade suave no início e fim da música')
                        trilha.change(lambda nome: str(escolher_musica(nome)) if nome not in ('Sem música','Arquivo próprio') else None,inputs=trilha,outputs=musica_preview)
                        arquivo_musica.change(lambda arq: arq,inputs=arquivo_musica,outputs=musica_preview)

                    with gr.Accordion('🔊 Efeitos sonoros programáveis · Opcional',open=False):
                        gr.Markdown('Escolha o efeito, o **momento no vídeo final** em `MM:SS` (ou `MM:SS.mmm`) e o volume. Cada efeito toca uma vez, a partir do horário indicado.')
                        efeito_preview_nome=gr.Dropdown(choices=list(EFFECTS),value=EFFECTS[0],label='▶ Ouvir efeito da biblioteca')
                        efeito_preview_audio=gr.Audio(label='Prévia do efeito',interactive=False,value=str(EFFECT_DIR/(EFFECTS[0]+'.wav')))
                        efeito_preview_nome.change(lambda nome: str(EFFECT_DIR/(nome+'.wav')),efeito_preview_nome,efeito_preview_audio)
                        fx_controles=[]
                        fx_grupos=[]
                        MAX_FX=12
                        for i_fx in range(MAX_FX):
                            with gr.Group(visible=(i_fx==0),elem_classes=['jw-zoom-item']) as fx_grupo:
                                gr.Markdown(f'**Efeito {i_fx+1}**')
                                with gr.Row():
                                    fx_nome=gr.Dropdown(choices=list(EFFECTS),value=EFFECTS[0],label='Efeito sonoro',interactive=True)
                                    fx_inicio=gr.Textbox(value='00:03',label='Momento (MM:SS)',interactive=True)
                                    fx_volume=gr.Slider(minimum=0,maximum=100,step=5,value=70,label='Volume (%)')
                                fx_ativo=gr.State(i_fx==0)
                                fx_controles.extend([fx_ativo,fx_nome,fx_inicio,fx_volume])
                                fx_grupos.append(fx_grupo)
                        fx_quantidade=gr.State(1)
                        with gr.Row():
                            fx_adicionar=gr.Button('＋ Adicionar efeito',variant='primary')
                            fx_remover=gr.Button('− Remover último efeito',variant='secondary')
                        def _alterar_qtd_fx(qtd,delta):
                            novo=max(1,min(MAX_FX,int(qtd)+delta))
                            return [novo]+[gr.update(visible=i<novo) for i in range(MAX_FX)]+[i<novo for i in range(MAX_FX)]
                        fx_saidas=[fx_quantidade]+fx_grupos+fx_controles[::4]
                        fx_adicionar.click(lambda n:_alterar_qtd_fx(n,1),fx_quantidade,fx_saidas,queue=False)
                        fx_remover.click(lambda n:_alterar_qtd_fx(n,-1),fx_quantidade,fx_saidas,queue=False)
                        gr.Markdown('Até 12 efeitos por vídeo. Os efeitos podem coincidir no tempo e são misturados com a música e a voz.')

                with gr.Column(scale=1, min_width=300):
                    with gr.Accordion('🎨 Filtros e cor · Opcional',open=False):
                        gr.Markdown('Escolha um estilo de cor para o vídeo final. Intensidade 0% desativa o preset, mantendo os ajustes manuais de brilho e contraste.')
                        filtro_video=gr.Dropdown(choices=list(FILTROS),value='Original',label='🎨 Filtro visual')
                        intensidade_filtro=gr.Slider(minimum=0,maximum=100,step=5,value=60,label='Intensidade do filtro (%)')
                        brilho_filtro=gr.Slider(minimum=-100,maximum=100,step=5,value=0,label='☀️ Brilho')
                        contraste_filtro=gr.Slider(minimum=-100,maximum=100,step=5,value=0,label='◐ Contraste')
            gr.Markdown('### ④ Baixe seu vídeo editado',elem_classes=['jw-section-heading'])
            aplicar=gr.Button('✦ Gerar meu vídeo',variant='primary',visible=False,elem_id='export-action')
            progresso_individual=gr.HTML(label='Progresso da edição')
            status=gr.Markdown(visible=False)
            resultado=gr.Video(label='Confira seu vídeo editado',format='mp4',visible=False,elem_id='jw-final-video')
            pronto_individual=gr.HTML('<section class="jw-ready" role="status"><h3>✓ Seu vídeo está pronto para baixar!</h3><p>⬇ Na caixa amarela logo abaixo, clique no nome do arquivo MP4 ou no ícone de download. O arquivo de legendas também estará disponível quando solicitado.</p></section>',visible=False)
            download=gr.File(label='⬇ DOWNLOAD — Clique para baixar o vídeo MP4',visible=False,elem_id='download-video')
            arquivo_srt=gr.File(label='Baixar arquivo de legendas SRT',visible=False)
            analisar.click(analisar_guiado,[video,prompt],[identificador,resumo,cortes,transcricao,aplicar],concurrency_limit=1)
            with gr.Group(visible=False) as instagram_panel:
                gr.Markdown('### 📱 Social Manager JW — Instagram Reels')
                gr.Markdown('**Deseja publicar o vídeo editado no Instagram?** Opcional. O download acima continua disponível.')
                gr.Markdown('### Conexão segura com Instagram')
                gr.Markdown('O token da Meta permanece no servidor. Publicação experimental somente no ambiente local.')
                with gr.Row():
                    ig_oauth_conectar = gr.Button('🔗 Conectar Instagram', variant='primary')
                    ig_oauth_status = gr.Button('🔄 Verificar conexão')
                    ig_oauth_desconectar = gr.Button('Desconectar')
                ig_oauth_mensagem = gr.Markdown('Clique em **Verificar conexão** para consultar a conta autorizada.')
                def _ig_oauth_conectar():
                    try:
                        url = conectar_instagram()
                        webbrowser.open(url, new=2)
                        return '🔗 Autorização aberta no navegador. Após concluir, clique em **Verificar conexão**.'
                    except InstagramOAuthClientError as exc:
                        return f'❌ {exc}'
                def _ig_oauth_status():
                    try:
                        dados = status_instagram()
                        if dados.get('connected'):
                            return f"✅ Instagram conectado: **@{dados.get('username') or 'conta autorizada'}** (ID: `{dados.get('instagram_id') or 'indisponível'}`)."
                        return 'ℹ️ Nenhuma conta Instagram conectada a esta licença/dispositivo.'
                    except InstagramOAuthClientError as exc:
                        return f'❌ {exc}'
                def _ig_oauth_desconectar():
                    try:
                        desconectar_instagram()
                        return '✅ Conexão removida do servidor local. Isso não revoga o acesso na Meta.'
                    except InstagramOAuthClientError as exc:
                        return f'❌ {exc}'
                ig_oauth_conectar.click(_ig_oauth_conectar, outputs=ig_oauth_mensagem)
                ig_oauth_status.click(_ig_oauth_status, outputs=ig_oauth_mensagem)
                ig_oauth_desconectar.click(_ig_oauth_desconectar, outputs=ig_oauth_mensagem)
                gr.Markdown('### Publicar Reel — teste local')
                ig_caption_nova = gr.Textbox(label='Legenda do Reel', lines=3, placeholder='Descrição e hashtags')
                ig_job_novo = gr.State(value=None)
                ig_pronto_novo = gr.State(value=False)
                ig_resultado_novo = gr.Markdown('Primeiro exporte o vídeo e prepare o Reel. Nada será publicado automaticamente.')
                with gr.Row():
                    ig_preparar_novo = gr.Button('📤 Preparar Reel (não publica)')
                    ig_verificar_novo = gr.Button('🔄 Verificar processamento')
                ig_confirmar_novo = gr.Checkbox(label='Confirmo que desejo publicar este Reel na conta Instagram conectada.', value=False)
                ig_publicar_novo = gr.Button('🚀 Publicar Reel agora', variant='primary', interactive=False)
                def _ig_nova_preparacao(video_path, caption):
                    try:
                        if not video_path:
                            raise InstagramOAuthClientError('Exporte um vídeo antes de preparar o Reel.')
                        dados = preparar_reel_servidor(str(video_path), caption or '')
                        job = dados['job_id']
                        criar_container_reel(job)
                        return job, False, '⏳ Vídeo enviado. A Meta está processando; clique em Verificar processamento.', gr.update(value=False), gr.update(interactive=False)
                    except (InstagramOAuthClientError, KeyError, ValueError) as exc:
                        return None, False, f'❌ {exc}', gr.update(value=False), gr.update(interactive=False)
                def _ig_nova_verificacao(job):
                    if not job:
                        return False, '⚠️ Prepare o Reel primeiro.', gr.update(value=False), gr.update(interactive=False)
                    try:
                        dados = consultar_reel(job)
                        ready = bool(dados.get('ready'))
                        return ready, ('✅ Reel pronto. Confirme a publicação.' if ready else f"⏳ Estado: {dados.get('state', 'UNKNOWN')}"), gr.update(value=False), gr.update(interactive=False)
                    except InstagramOAuthClientError as exc:
                        return False, f'❌ {exc}', gr.update(value=False), gr.update(interactive=False)
                def _ig_nova_confirmacao(confirmado, pronto):
                    return gr.update(interactive=bool(confirmado and pronto))
                def _ig_nova_publicacao(job, confirmado, pronto):
                    if not (job and confirmado and pronto):
                        return '⚠️ Verifique o processamento e confirme a publicação.', job, pronto, gr.update(value=False), gr.update(interactive=False)
                    try:
                        dados = publicar_reel_servidor(job)
                        return f"✅ Reel publicado! ID: `{dados['media_id']}`", None, False, gr.update(value=False), gr.update(interactive=False)
                    except (InstagramOAuthClientError, KeyError) as exc:
                        return f'❌ {exc} Não clique novamente sem verificar o resultado na Meta.', job, False, gr.update(value=False), gr.update(interactive=False)
                ig_preparar_novo.click(_ig_nova_preparacao, [download, ig_caption_nova], [ig_job_novo, ig_pronto_novo, ig_resultado_novo, ig_confirmar_novo, ig_publicar_novo], concurrency_limit=1)
                ig_verificar_novo.click(_ig_nova_verificacao, [ig_job_novo], [ig_pronto_novo, ig_resultado_novo, ig_confirmar_novo, ig_publicar_novo], concurrency_limit=1)
                ig_confirmar_novo.change(_ig_nova_confirmacao, [ig_confirmar_novo, ig_pronto_novo], [ig_publicar_novo], queue=False)
                ig_publicar_novo.click(_ig_nova_publicacao, [ig_job_novo, ig_confirmar_novo, ig_pronto_novo], [ig_resultado_novo, ig_job_novo, ig_pronto_novo, ig_confirmar_novo, ig_publicar_novo], concurrency_limit=1)
            aplicar.click(aplicar_com_progresso,[identificador,cortes,ativar_legendas,estilo,visual,tamanho,posicao,transicao,duracao_transicao,trilha,arquivo_musica,volume_musica,manter_audio,fade_musica,filtro_video,intensidade_filtro,brilho_filtro,contraste_filtro,cortes_manuais,modo_legendas,legendas_manuais]+zoom_controles+fx_controles,[progresso_individual,resultado,download,arquivo_srt,status,pronto_individual,instagram_panel],concurrency_limit=1)
            aplicar.click(lambda: (None, False, '', gr.update(value=False), gr.update(interactive=False)), outputs=[ig_job_novo,ig_pronto_novo,ig_resultado_novo,ig_confirmar_novo,ig_publicar_novo], queue=False)

            for entrada in (video,prompt):
                entrada.change(limpar_analise,outputs=[identificador,resumo,cortes,transcricao,aplicar])
        with gr.Tab('▦ Vários vídeos'):
            gr.Markdown('### ① Importe seus vídeos',elem_classes=['jw-section-heading'])
            gr.Markdown('Selecione de 1 a 20 arquivos MP4 ou MOV. Você pode misturar os formatos no mesmo lote.',elem_classes=['helper'])
            arquivos_lote=gr.File(label='Selecionar vídeos MP4 ou MOV',file_count='multiple',file_types=['.mp4','.mov'],type='filepath')
            gr.Markdown('### ② Descreva a edição para todos',elem_classes=['jw-section-heading'])
            prompt_lote=gr.Textbox(label='O que fazer em cada vídeo?',lines=3,placeholder='Ex.: Remova silêncios maiores que 2 segundos e melhore o áudio de todos os vídeos.')
            exemplo_lote=gr.Dropdown(choices=list(EXEMPLOS),label='Ou escolha uma sugestão pronta',value=None)
            exemplo_lote.change(preencher_exemplo,exemplo_lote,prompt_lote)
            legendas_lote=gr.Checkbox(label='Adicionar legendas a todos os vídeos',value=False)
            estilo_lote=gr.Radio(choices=['Tradicional','Dinâmica'],value='Tradicional',label='Estilo das legendas',visible=False)
            with gr.Column(visible=False) as aparencia_lote:
                visual_lote=gr.Dropdown(choices=list(ESTILOS_VISUAIS),value='Clássica',label='Estilo visual (todos os vídeos)')
                tamanho_lote=gr.Slider(minimum=60,maximum=160,step=10,value=100,label='Tamanho (%)')
                posicao_lote=gr.Radio(choices=['Inferior','Centro','Superior'],value='Inferior',label='Posição')
            legendas_lote.change(lambda x: (gr.update(visible=x),gr.update(visible=x)),legendas_lote,[estilo_lote,aparencia_lote])
            gr.Markdown('**Acabamento do vídeo**  ·  Escolha apenas os recursos que quiser usar.',elem_classes=['jw-subsection'])
            with gr.Row(equal_height=False, elem_classes=['jw-settings-grid']):
                with gr.Column(scale=1, min_width=300):
                    with gr.Accordion('✨ Transições · Opcional',open=False):
                        gr.Markdown('Cada vídeo recebe o efeito entre seus próprios cortes preservados. Os arquivos continuam sendo exportados separadamente; vídeos com um único trecho não precisam de transição.')
                        transicao_lote=gr.Radio(choices=['Nenhuma','Dissolver','Fade para preto','Deslizar'],value='Nenhuma',label='Efeito para todos os vídeos')
                        duracao_transicao_lote=gr.Slider(minimum=0.2,maximum=2.0,step=0.1,value=0.7,label='Duração por transição (segundos)')
                    with gr.Accordion('🎵 Música de fundo · Opcional',open=False):
                        gr.Markdown('Trilhas instrumentais originais incluídas no aplicativo, ou importe sua própria música. A trilha é aplicada ao vídeo exportado.')
                        trilha_lote=gr.Dropdown(choices=list(TRACKS),value='Sem música',label='🎼 Escolha uma música')
                        with gr.Row():
                            musica_preview_lote=gr.Audio(label='▶️ Ouvir a trilha selecionada',interactive=False)
                            arquivo_musica_lote=gr.File(label='📁 Importar música própria (MP3/WAV/M4A...)',file_types=['.mp3','.wav','.m4a','.aac','.flac','.ogg'],type='filepath')
                        volume_musica_lote=gr.Slider(minimum=0,maximum=100,step=5,value=20,label='🔊 Volume da música (%)')
                        manter_audio_lote=gr.Checkbox(value=True,label='🎙️ Manter o áudio original do vídeo')
                        fade_musica_lote=gr.Checkbox(value=True,label='🌅 Fade suave no início e fim da música')
                        trilha_lote.change(lambda nome: str(escolher_musica(nome)) if nome not in ('Sem música','Arquivo próprio') else None,inputs=trilha_lote,outputs=musica_preview_lote)
                        arquivo_musica_lote.change(lambda arq: arq,inputs=arquivo_musica_lote,outputs=musica_preview_lote)
                with gr.Column(scale=1, min_width=300):
                    with gr.Accordion('🎨 Filtros e cor · Opcional',open=False):
                        gr.Markdown('Escolha um estilo de cor para todos os vídeos. Intensidade 0% desativa o preset, mantendo os ajustes manuais de brilho e contraste.')
                        filtro_video_lote=gr.Dropdown(choices=list(FILTROS),value='Original',label='🎨 Filtro visual')
                        intensidade_filtro_lote=gr.Slider(minimum=0,maximum=100,step=5,value=60,label='Intensidade do filtro (%)')
                        brilho_filtro_lote=gr.Slider(minimum=-100,maximum=100,step=5,value=0,label='☀️ Brilho')
                        contraste_filtro_lote=gr.Slider(minimum=-100,maximum=100,step=5,value=0,label='◐ Contraste')
            gr.Markdown('**Atenção:** o modo em lote aprova os cortes automaticamente. Para revisar cada corte, use “Editar um vídeo”.')
            iniciar_lote=gr.Button('✦ Gerar vídeos do lote',variant='primary',elem_id='export-action-batch')
            gr.Markdown('### ④ Baixe seus vídeos editados',elem_classes=['jw-section-heading'])
            progresso_lote=gr.HTML(label='Progresso de cada vídeo')
            status_lote=gr.Markdown(visible=False)
            pronto_lote=gr.HTML('<section class="jw-ready" role="status"><h3>✓ Seus vídeos estão prontos para baixar!</h3><p>⬇ Na caixa amarela abaixo, clique no arquivo ZIP ou no ícone de download para salvar todos os vídeos editados. Confira o relatório para identificar eventuais falhas individuais.</p></section>',visible=False)
            download_lote=gr.File(label='⬇ DOWNLOAD — Clique para baixar o pacote ZIP',visible=False,elem_id='download-batch')
            iniciar_lote.click(lote_com_progresso,[arquivos_lote,prompt_lote,legendas_lote,estilo_lote,visual_lote,tamanho_lote,posicao_lote,transicao_lote,duracao_transicao_lote,trilha_lote,arquivo_musica_lote,volume_musica_lote,manter_audio_lote,fade_musica_lote,filtro_video_lote,intensidade_filtro_lote,brilho_filtro_lote,contraste_filtro_lote],[progresso_lote,download_lote,status_lote,pronto_lote],concurrency_limit=1)
    gr.HTML('<footer id="jw-footer"><strong>EditAI Videos JW</strong><div>Desenvolvido por Jonathan Willian Gonçales Alves</div><small>Versão 0.9.8 Beta • Edição inteligente de vídeos • Processamento local</small></footer>')
app.queue(default_concurrency_limit=1,max_size=10)

def iniciar():
    estilo_launch = {'css': CSS, 'theme': gr.themes.Base(primary_hue=gr.themes.colors.yellow, neutral_hue=gr.themes.colors.slate)} if _GRADIO6 else {}
    app.launch(server_name='127.0.0.1', server_port=7860, inbrowser=True, share=False,
               show_error=True, allowed_paths=[str(SAIDAS.resolve()),str((Path(__file__).resolve().parents[1] / "music").resolve())], **estilo_launch)
