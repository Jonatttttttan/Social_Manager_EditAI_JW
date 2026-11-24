
from promptvideo.core.templates import carregar_template


def preparar_template(identificador, validador):
    """Carrega e valida uma configuracao nativa."""

    template = carregar_template(identificador)

    configuracoes = validador(
        template["configuracoes"]
    )

    return template["nome"], configuracoes


def adaptar_template_individual(identificador, validador):
    """Adapta o template para a edicao individual."""

    nome, configuracoes = preparar_template(
        identificador,
        validador,
    )

    dados = dict(configuracoes)

    dados["modo_legendas"] = (
        "Autom\u00e1ticas"
        if dados["legendas"]
        else "Sem legendas"
    )

    dados["exibir_legendas_manuais"] = False

    dados["exibir_controles_legendas"] = (
        dados["legendas"]
    )

    dados["exibir_limite_silencio"] = (
        dados["eliminar_silencios"]
    )

    return nome, dados


def adaptar_template_lote(identificador, validador):
    """Adapta o template para a edicao em lote."""

    nome, configuracoes = preparar_template(
        identificador,
        validador,
    )

    dados = dict(configuracoes)

    dados["exibir_controles_legendas"] = (
        dados["legendas"]
    )

    dados["exibir_limite_silencio"] = (
        dados["eliminar_silencios"]
    )

    return nome, dados
