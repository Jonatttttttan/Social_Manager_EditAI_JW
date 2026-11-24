import gradio as gr

from promptvideo.ui.template_previews import gerar_cartoes_templates

from promptvideo.core.templates import (
    listar_categorias,
    listar_templates,
    carregar_template,
)


CSS_TEMPLATES = """

.jw-template-panel .prose code {
    background: #242832 !important;
    color: #facc15 !important;
    border: 1px solid #363b45;
    border-radius: 4px;
    padding: 2px 5px;
}

.jw-template-panel .block > label > span,
.jw-template-panel .block-label,
.jw-template-panel legend {
    color: #cbd5e1 !important;
}



.jw-template-card {
    cursor: pointer;
    transition: border-color .2s, transform .2s;
}

.jw-template-card:hover {
    transform: translateY(-2px);
    border-color: #facc15 !important;
}

.jw-template-card.jw-selected {
    border: 2px solid #facc15 !important;
    box-shadow: 0 0 0 1px #facc15;
}

.jw-template-card:focus-visible {
    outline: 2px solid #facc15;
}

.jw-template-panel legend,
.jw-template-panel .block-label {
    color: #cbd5e1 !important;
}


.jw-template-panel {
    --body-text-color: #f4f7ff;
    --body-text-color-subdued: #aeb8c8;
    --background-fill-primary: #111318;
    --background-fill-secondary: #1c2028;
    --block-background-fill: #1c2028;
    --block-label-background-fill: #1c2028;
    --block-label-text-color: #cbd5e1;
    --border-color-primary: #363b45;
    --input-background-fill: #242832;
    --input-border-color: #363b45;
    --input-border-color-focus: #facc15;
    color: #f4f7ff !important;
}

.jw-template-panel .block,
.jw-template-panel .form,
.jw-template-panel .prose {
    background: #111318 !important;
    color: #f4f7ff !important;
}

.jw-template-panel .prose p,
.jw-template-panel .prose h3,
.jw-template-panel .prose strong {
    color: #f4f7ff !important;
}

.jw-template-categories label,
.jw-template-options label {
    background: #242832 !important;
    color: #f4f7ff !important;
    border: 1px solid #363b45 !important;
    border-radius: 8px !important;
}

.jw-template-categories label:has(input:checked),
.jw-template-options label:has(input:checked) {
    background: #facc15 !important;
    color: #111318 !important;
    border-color: #facc15 !important;
}

.jw-template-panel input[type="radio"] {
    accent-color: #eab308;
}

.jw-template-panel button.primary {
    color: #111318 !important;
    background: #facc15 !important;
}


.jw-template-panel {
    background: #111318 !important;
    border: 1px solid #363b45 !important;
    border-radius: 14px !important;
    padding: 16px !important;
}

.jw-template-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 10px 0;
}

.jw-template-card {
    min-width: 0;
    background: #1c2028;
    border: 1px solid #363b45;
    border-radius: 12px;
    padding: 10px;
    color: #f4f7ff;
    transition: border-color .2s;
}

.jw-template-card:hover {
    border-color: #facc15;
}

.jw-template-preview {
    max-width: 150px;
    margin: 0 auto 10px;
}

.jw-template-preview svg {
    display: block;
    width: 100%;
    height: auto;
}

.jw-template-card strong {
    display: block;
    text-align: center;
    color: #facc15;
    font-size: 15px;
}

.jw-template-card small {
    display: block;
    text-align: center;
    color: #cbd5e1;
    font-size: 12px;
    margin-top: 4px;
}

.jw-template-card p {
    color: #aeb8c8;
    font-size: 12px;
    margin-top: 8px;
    line-height: 1.4;
}

@media (max-width: 640px) {
    .jw-template-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
"""


def atualizar_previa_categoria(categoria):
    return gerar_cartoes_templates(categoria)


def opcoes_templates(categoria):
    return [
        (template["nome"], identificador)
        for identificador, template
        in listar_templates(categoria).items()
    ]


def atualizar_categoria(categoria):
    return gr.update(
        choices=opcoes_templates(categoria),
        value=None,
    )


def descrever_template(identificador):
    if not identificador:
        return "Selecione um template."

    template = carregar_template(identificador)

    return (
        f"**{template['nome']}**\n\n"
        f"{template['descricao']}"
    )


def criar_seletor_templates():
    categorias = listar_categorias()

    with gr.Group(elem_classes=["jw-template-panel"]):
        gr.Markdown("### Templates EditAI")

        gr.Markdown(
            "Escolha um estilo de edição e personalize "
            "as configurações conforme sua necessidade."
        )

        categoria = gr.Radio(
            choices=categorias,
            value=categorias[0],
            label="Categoria",
            interactive=True,
            elem_classes=["jw-template-categories"],
        )

        js_cartoes = """
        const painel = element.closest('.jw-template-panel');

        if (painel) {
            const atualizarDestaque = () => {
                const radios = Array.from(
                    painel.querySelectorAll(
                        '.jw-template-options input[type="radio"]'
                    )
                );

                const cartoes = Array.from(
                    element.querySelectorAll('.jw-template-card')
                );

                cartoes.forEach((cartao, indice) => {
                    const selecionado = Boolean(radios[indice]?.checked);

                    cartao.classList.toggle(
                        'jw-selected', selecionado
                    );

                    cartao.setAttribute('role', 'button');
                    cartao.setAttribute('tabindex', '0');
                    cartao.setAttribute(
                        'aria-pressed', String(selecionado)
                    );
                });
            };

            const selecionarCartao = (cartao) => {
                const cartoes = Array.from(
                    element.querySelectorAll('.jw-template-card')
                );

                const indice = cartoes.indexOf(cartao);

                const radios = Array.from(
                    painel.querySelectorAll(
                        '.jw-template-options input[type="radio"]'
                    )
                );

                if (indice >= 0 && radios[indice]) {
                    radios[indice].click();
                    atualizarDestaque();
                }
            };

            element.addEventListener('click', (evento) => {
                const cartao = evento.target.closest(
                    '.jw-template-card'
                );

                if (cartao) selecionarCartao(cartao);
            });

            element.addEventListener('keydown', (evento) => {
                const cartao = evento.target.closest(
                    '.jw-template-card'
                );

                if (cartao && (
                    evento.key === 'Enter' ||
                    evento.key === ' '
                )) {
                    evento.preventDefault();
                    selecionarCartao(cartao);
                }
            });

            painel.addEventListener(
                'change', atualizarDestaque
            );

            const observador = new MutationObserver(
                atualizarDestaque
            );

            observador.observe(painel, {
                childList: true,
                subtree: true
            });

            atualizarDestaque();
        }
        """

        previa = gr.HTML(
            js_on_load=js_cartoes,
            value=gerar_cartoes_templates(categorias[0]),
            elem_classes=["jw-template-gallery"],
        )

        template = gr.Radio(
            choices=opcoes_templates(categorias[0]),
            value=None,
            label="Templates disponíveis",
            interactive=True,
            elem_classes=["jw-template-options"],
        )

        descricao = gr.Markdown(
            "Selecione um template."
        )

        aplicar = gr.Button(
            "Aplicar template",
            variant="primary",
        )

        status = gr.Markdown("")

        categoria.change(
            fn=atualizar_categoria,
            inputs=categoria,
            outputs=template,
        )

        categoria.change(
            fn=atualizar_previa_categoria,
            inputs=categoria,
            outputs=previa,
        )

        categoria.change(
            fn=lambda: "",
            inputs=None,
            outputs=status,
            queue=False,
        )

        template.change(
            fn=lambda: "",
            inputs=None,
            outputs=status,
            queue=False,
        )

        template.change(
            fn=descrever_template,
            inputs=template,
            outputs=descricao,
        )

    return {
        "previa": previa,
        "categoria": categoria,
        "template": template,
        "descricao": descricao,
        "aplicar": aplicar,
        "status": status,
    }
