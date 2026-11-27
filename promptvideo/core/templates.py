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
    "abertura": "Nenhuma",
    "duracao_abertura": 1.0,
    "encerramento": "Nenhuma",
    "duracao_encerramento": 1.0,
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
        'Reduz pausas com limite de 1s, usa legendas grandes, música energética e cores vibrantes.',
        segundos_silencio=1,
        estilo="Din\u00e2mica",
        visual="Shorts",
        tamanho=130,
        trilha="Energia Positiva",
        volume_musica=18,
        filtro_video="Vibrante",
        intensidade_filtro=65,
        contraste_filtro=10,
    ),

    "viral_pulso": _criar_template(
        "Viral", "Pulso",
        'Reduz pausas, destaca palavras durante a fala e adiciona música tecnológica.',
        segundos_silencio=1,
        estilo="Din\u00e2mica",
        visual="Palavra destacada",
        tamanho=120,
        trilha="Pulso Tecnol\u00f3gico",
        volume_musica=15,
        filtro_video="Vibrante",
        intensidade_filtro=55,
    ),

    "viral_neon": _criar_template(
        "Viral", "Neon",
        'Combina legendas luminosas, música digital e tonalidades cinematográficas frias.',
        segundos_silencio=1,
        estilo="Din\u00e2mica",
        visual="Neon",
        tamanho=115,
        trilha="Aurora Digital",
        volume_musica=18,
        filtro_video="Cinematogr\u00e1fico frio",
        intensidade_filtro=55,
    ),

    # LIMPO
    "limpo_essencial": _criar_template(
        "Limpo", "Essencial",
        'Limpa o áudio, reduz pausas e adiciona legendas clássicas, sem música ou filtro visual.',
        segundos_silencio=2,
        visual="Cl\u00e1ssica",
        tamanho=90,
        volume_musica=0,
    ),

    "limpo_elegante": _criar_template(
        "Limpo", "Elegante",
        'Legendas discretas, piano suave e tratamento visual leve.',
        visual="Minimalista",
        tamanho=85,
        trilha="Piano Calmo",
        volume_musica=10,
        filtro_video="Suave",
        intensidade_filtro=35,
    ),

    "limpo_minimalista": _criar_template(
        "Limpo", "Minimalista",
        'Legendas pequenas, música ambiente e preservação das cores originais.',
        visual="Minimalista",
        tamanho=80,
        trilha="Ambient Suave",
        volume_musica=8,
    ),

    # CONVERSA
    "conversa_podcast": _criar_template(
        "Conversa", "Podcast",
        'Valoriza a fala com palavras destacadas, redução de pausas longas e sem música.',
        segundos_silencio=3,
        estilo="Din\u00e2mica",
        visual="Palavra destacada",
        tamanho=110,
        volume_musica=0,
    ),

    "conversa_dialogo": _criar_template(
        "Conversa", "Di\u00e1logo",
        'Preserva as pausas naturais da conversa, com legendas clássicas e filtro suave.',
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
        'Legendas em caixa moderna, redução de pausas longas e sem música adicional.',
        segundos_silencio=4,
        visual="Caixa moderna",
        tamanho=95,
        volume_musica=0,
    ),

    # TUTORIAL
    "tutorial_professor": _criar_template(
        "Tutorial", "Professor",
        'Legendas clássicas maiores e música discreta para aulas e explicações.',
        segundos_silencio=3,
        visual="Cl\u00e1ssica",
        tamanho=105,
        trilha="Foco Criativo",
        volume_musica=8,
    ),

    "tutorial_passo_a_passo": _criar_template(
        "Tutorial", "Passo a passo",
        'Legendas em caixa moderna, cores vibrantes e música leve para demonstrações.',
        visual="Caixa moderna",
        tamanho=110,
        trilha="Inspira\u00e7\u00e3o Leve",
        volume_musica=10,
        filtro_video="Vibrante",
        intensidade_filtro=30,
    ),

    "tutorial_ciencia": _criar_template(
        "Tutorial", "Ci\u00eancia",
        'Destaca palavras durante a explicação e adiciona trilha documental.',
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
        'Legendas minimalistas, música leve e filtro suave para o cotidiano.',
        segundos_silencio=3,
        visual="Minimalista",
        tamanho=90,
        trilha="Energia Leve",
        volume_musica=15,
        filtro_video="Suave",
        intensidade_filtro=40,
    ),

    "vlog_viagem": _criar_template(
        "Vlog", "Viagem",
        'Preserva pausas originais, adiciona música e tonalidades cinematográficas quentes.',
        eliminar_silencios=False,
        segundos_silencio=3,
        visual="Cl\u00e1ssica",
        tamanho=85,
        trilha="Viagem Serena",
        volume_musica=20,
        filtro_video="Cinematogr\u00e1fico quente",
        intensidade_filtro=55,
    ),

    "vlog_cinema": _criar_template(
        "Vlog", "Cinema",
        'Tonalidades frias, contraste reforcado, música cinematográfica e legendas discretas.',
        eliminar_silencios=False,
        segundos_silencio=4,
        visual="Minimalista",
        tamanho=80,
        trilha="Noite Cinem\u00e1tica",
        volume_musica=18,
        filtro_video="Cinematogr\u00e1fico frio",
        intensidade_filtro=60,
        contraste_filtro=8,
    ),
})
