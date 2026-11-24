from html import escape

from promptvideo.core.templates import listar_templates


CORES_FILTROS = {
    "Original": ("#334155", "#111827"),
    "Cinematogr\u00e1fico quente": ("#795332", "#292018"),
    "Cinematogr\u00e1fico frio": ("#244762", "#101827"),
    "Preto e branco": ("#525252", "#171717"),
    "Vintage": ("#756047", "#30271f"),
    "Vibrante": ("#575027", "#1c2538"),
    "Suave": ("#657783", "#28343d"),
}


def gerar_previa_svg(template):
    config = template["configuracoes"]
    visual = config["visual"]

    cor1, cor2 = CORES_FILTROS.get(
        config["filtro_video"],
        CORES_FILTROS["Original"],
    )

    cor_texto = "#ffffff"
    fundo_legenda = "transparent"
    peso = "700"

    if visual == "Shorts":
        cor_texto = "#facc15"
        peso = "900"
    elif visual == "Palavra destacada":
        fundo_legenda = "#facc15"
        cor_texto = "#111827"
    elif visual == "Caixa moderna":
        fundo_legenda = "#111827"
    elif visual == "Minimalista":
        peso = "400"
    elif visual == "Neon":
        cor_texto = "#67e8f9"
        peso = "900"

    tamanho = max(
        9, min(15, config["tamanho"] / 9)
    )

    posicao = {
        "Superior": 30,
        "Centro": 96,
        "Inferior": 151,
    }.get(config["posicao"], 151)

    return f"""
    <svg viewBox="0 0 108 192"
         xmlns="http://www.w3.org/2000/svg"
         role="img"
         aria-label="Previa ilustrativa">
        <rect width="108" height="192"
              rx="7" fill="{cor2}"/>
        <rect width="108" height="100"
              rx="7" fill="{cor1}"/>
        <circle cx="54" cy="62" r="24"
                fill="#ffffff" opacity=".18"/>
        <path d="M14 145 Q14 91 54 91 Q94 91 94 145"
              fill="#ffffff" opacity=".15"/>
        <rect x="8" y="8" width="42" height="13"
              rx="3" fill="#111827"/>
        <text x="29" y="17" fill="#ffffff"
              font-size="7" text-anchor="middle">
            EDITAI
        </text>
        <rect x="7" y="{posicao - 13}"
              width="94" height="21" rx="3"
              fill="{fundo_legenda}"/>
        <text x="54" y="{posicao}"
              fill="{cor_texto}"
              font-family="Arial, sans-serif"
              font-size="{tamanho}"
              font-weight="{peso}"
              text-anchor="middle">
            SEU VIDEO
        </text>
    </svg>
    """


def gerar_cartoes_templates(categoria):
    cartoes = []

    for identificador, template in listar_templates(
        categoria
    ).items():
        nome = escape(template["nome"])
        descricao = escape(template["descricao"])
        visual = escape(
            template["configuracoes"]["visual"]
        )

        svg = gerar_previa_svg(template)

        cartoes.append(f"""
        <article class="jw-template-card"
                 data-template="{escape(identificador)}">
            <div class="jw-template-preview">
                {svg}
            </div>
            <strong>{nome}</strong>
            <small>{visual}</small>
            <p>{descricao}</p>
        </article>
        """)

    return (
        '<div class="jw-template-grid">'
        + "".join(cartoes)
        + "</div>"
    )
