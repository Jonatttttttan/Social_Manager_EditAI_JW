from copy import deepcopy

CATEGORIAS_TEMPLATES = (
    "Viral",
    "Limpo",
    "Conversa",
    "Tutorial",
    "Vlog",
)

CONFIGURACAO_PADRAO = {
    "reduzir_ruido": True,
    "eliminar_silencios": True,
    "segundos_silencio": 2,
    "melhorar_audio": True,
    "legendas": True,
    "estilo": "Tradicional",
    "visual": "Cl\u00e1ssica",
    "tamanho": 100,
    "posicao": "Inferior",
    "transicao": "Nenhuma",
    "duracao_transicao": 0.5,
    "trilha": "Sem m\u00fasica",
    "arquivo_musica": None,
    "volume_musica": 15,
    "manter_audio": True,
    "fade_musica": True,
    "filtro_video": "Original",
    "intensidade_filtro": 50,
    "brilho_filtro": 0,
    "contraste_filtro": 0,
}

_TEMPLATES = {}


def _criar_template(categoria, nome, descricao, **ajustes):
    if categoria not in CATEGORIAS_TEMPLATES:
        raise ValueError("Categoria invalida.")

    desconhecidos = set(ajustes) - set(CONFIGURACAO_PADRAO)

    if desconhecidos:
        raise ValueError(
            f"Parametros desconhecidos: {desconhecidos}"
        )

    configuracoes = deepcopy(CONFIGURACAO_PADRAO)
    configuracoes.update(ajustes)

    return {
        "categoria": categoria,
        "nome": nome,
        "descricao": descricao,
        "configuracoes": configuracoes,
    }


def listar_categorias():
    return list(CATEGORIAS_TEMPLATES)


def listar_templates(categoria=None):
    if categoria is not None:
        if categoria not in CATEGORIAS_TEMPLATES:
            raise ValueError("Categoria invalida.")

    return {
        identificador: deepcopy(template)
        for identificador, template in _TEMPLATES.items()
        if categoria is None
        or template["categoria"] == categoria
    }


def carregar_template(identificador):
    if identificador not in _TEMPLATES:
        raise ValueError("Template nao encontrado.")

    return deepcopy(_TEMPLATES[identificador])


def carregar_configuracao_template(identificador):
    return carregar_template(identificador)["configuracoes"]


_TEMPLATES.update({
    # VIRAL
    "viral_impacto": _criar_template(
        "Viral", "Impacto",
        "Edição energética para vídeos curtos.",
        segundos_silencio=1,
        estilo="Din\u00e2mica",
        visual="Shorts",
        tamanho=130,
        transicao="Deslizar",
        duracao_transicao=0.2,
        trilha="Energia Positiva",
        volume_musica=18,
        filtro_video="Vibrante",
        intensidade_filtro=65,
        contraste_filtro=10,
    ),

    "viral_pulso": _criar_template(
        "Viral", "Pulso",
        "Ritmo acelerado e palavras em destaque.",
        segundos_silencio=1,
        estilo="Din\u00e2mica",
        visual="Palavra destacada",
        tamanho=120,
        transicao="Nenhuma",
        trilha="Pulso Tecnol\u00f3gico",
        volume_musica=15,
        filtro_video="Vibrante",
        intensidade_filtro=55,
    ),

    "viral_neon": _criar_template(
        "Viral", "Neon",
        "Estética digital e legendas luminosas.",
        segundos_silencio=1,
        estilo="Din\u00e2mica",
        visual="Neon",
        tamanho=115,
        transicao="Dissolver",
        duracao_transicao=0.3,
        trilha="Aurora Digital",
        volume_musica=18,
        filtro_video="Cinematogr\u00e1fico frio",
        intensidade_filtro=55,
    ),

    # LIMPO
    "limpo_essencial": _criar_template(
        "Limpo", "Essencial",
        "Edição natural, clara e profissional.",
        segundos_silencio=2,
        visual="Cl\u00e1ssica",
        tamanho=90,
        volume_musica=0,
    ),

    "limpo_elegante": _criar_template(
        "Limpo", "Elegante",
        "Visual discreto com acompanhamento de piano.",
        visual="Minimalista",
        tamanho=85,
        transicao="Dissolver",
        duracao_transicao=0.7,
        trilha="Piano Calmo",
        volume_musica=10,
        filtro_video="Suave",
        intensidade_filtro=35,
    ),

    "limpo_minimalista": _criar_template(
        "Limpo", "Minimalista",
        "Legendas discretas e atmosfera leve.",
        visual="Minimalista",
        tamanho=80,
        trilha="Ambient Suave",
        volume_musica=8,
    ),

    # CONVERSA
    "conversa_podcast": _criar_template(
        "Conversa", "Podcast",
        "Destaque para a fala e o conteúdo.",
        segundos_silencio=3,
        estilo="Din\u00e2mica",
        visual="Palavra destacada",
        tamanho=110,
        volume_musica=0,
    ),

    "conversa_dialogo": _criar_template(
        "Conversa", "Di\u00e1logo",
        "Preserva o ritmo natural da conversa.",
        eliminar_silencios=False,
        segundos_silencio=3,
        visual="Cl\u00e1ssica",
        tamanho=95,
        volume_musica=0,
        filtro_video="Suave",
        intensidade_filtro=25,
    ),

    "conversa_entrevista": _criar_template(
        "Conversa", "Entrevista",
        "Apresentação profissional de depoimentos.",
        segundos_silencio=4,
        visual="Caixa moderna",
        tamanho=95,
        transicao="Dissolver",
        duracao_transicao=0.5,
        volume_musica=0,
    ),

    # TUTORIAL
    "tutorial_professor": _criar_template(
        "Tutorial", "Professor",
        "Clareza para aulas e explicações.",
        segundos_silencio=3,
        visual="Cl\u00e1ssica",
        tamanho=105,
        trilha="Foco Criativo",
        volume_musica=8,
    ),

    "tutorial_passo_a_passo": _criar_template(
        "Tutorial", "Passo a passo",
        "Edição didática com destaque visual.",
        visual="Caixa moderna",
        tamanho=110,
        transicao="Dissolver",
        duracao_transicao=0.4,
        trilha="Inspira\u00e7\u00e3o Leve",
        volume_musica=10,
        filtro_video="Vibrante",
        intensidade_filtro=30,
    ),

    "tutorial_ciencia": _criar_template(
        "Tutorial", "Ci\u00eancia",
        "Estilo documental para conteúdo científico.",
        segundos_silencio=3,
        estilo="Din\u00e2mica",
        visual="Palavra destacada",
        tamanho=100,
        trilha="Document\u00e1rio Natural",
        volume_musica=10,
    ),

    # VLOG
    "vlog_lifestyle": _criar_template(
        "Vlog", "Lifestyle",
        "Edição leve para momentos do cotidiano.",
        segundos_silencio=3,
        visual="Minimalista",
        tamanho=90,
        transicao="Dissolver",
        duracao_transicao=0.5,
        trilha="Energia Leve",
        volume_musica=15,
        filtro_video="Suave",
        intensidade_filtro=40,
    ),

    "vlog_viagem": _criar_template(
        "Vlog", "Viagem",
        "Atmosfera acolhedora para paisagens e viagens.",
        eliminar_silencios=False,
        segundos_silencio=3,
        visual="Cl\u00e1ssica",
        tamanho=85,
        transicao="Dissolver",
        duracao_transicao=0.8,
        trilha="Viagem Serena",
        volume_musica=20,
        filtro_video="Cinematogr\u00e1fico quente",
        intensidade_filtro=55,
    ),

    "vlog_cinema": _criar_template(
        "Vlog", "Cinema",
        "Atmosfera cinematográfica e transições suaves.",
        eliminar_silencios=False,
        segundos_silencio=4,
        visual="Minimalista",
        tamanho=80,
        transicao="Fade para preto",
        duracao_transicao=1.0,
        trilha="Noite Cinem\u00e1tica",
        volume_musica=18,
        filtro_video="Cinematogr\u00e1fico frio",
        intensidade_filtro=60,
        contraste_filtro=8,
    ),
})
