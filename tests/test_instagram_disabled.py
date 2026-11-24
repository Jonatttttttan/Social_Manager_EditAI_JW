from unittest.mock import patch

import pytest

from promptvideo import config
from promptvideo.integrations import instagram as direto
from promptvideo.integrations import instagram_oauth_client as oauth


MENSAGEM = (
    "A integra\u00e7\u00e3o com o Instagram "
    "est\u00e1 desativada nesta vers\u00e3o do EditAI."
)


def test_instagram_desativado_por_padrao():
    assert config.INSTAGRAM_ENABLED is False
    assert direto.INSTAGRAM_ENABLED is False
    assert oauth.INSTAGRAM_ENABLED is False


@pytest.mark.parametrize(
    "funcao, argumentos, excecao",
    [
        pytest.param(
            direto._request_json,
            ("GET", "https://example.invalid", "token-ficticio"),
            direto.InstagramPublishError,
            id="direto-request-json"
        ),
        pytest.param(
            direto.preparar_reel,
            ("video-inexistente.mp4", "123", "token-ficticio"),
            direto.InstagramPublishError,
            id="direto-preparar"
        ),
        pytest.param(
            direto.status_reel,
            ("container-teste", "token-ficticio"),
            direto.InstagramPublishError,
            id="direto-status"
        ),
        pytest.param(
            direto.publicar_reel,
            ("123", "container-teste", "token-ficticio"),
            direto.InstagramPublishError,
            id="direto-publicar"
        ),
        pytest.param(
            oauth._call,
            ("GET", "/api/instagram/status"),
            oauth.InstagramOAuthClientError,
            id="oauth-call"
        ),
        pytest.param(
            oauth._reels_request,
            ("POST", "/api/instagram/reels/teste/publish"),
            oauth.InstagramOAuthClientError,
            id="oauth-reels-request"
        ),
        pytest.param(
            oauth.conectar_instagram,
            (),
            oauth.InstagramOAuthClientError,
            id="oauth-conectar"
        ),
        pytest.param(
            oauth.status_instagram,
            (),
            oauth.InstagramOAuthClientError,
            id="oauth-status"
        ),
        pytest.param(
            oauth.desconectar_instagram,
            (),
            oauth.InstagramOAuthClientError,
            id="oauth-desconectar"
        ),
        pytest.param(
            oauth.preparar_reel_servidor,
            ("video-inexistente.mp4", "Teste"),
            oauth.InstagramOAuthClientError,
            id="oauth-preparar"
        ),
        pytest.param(
            oauth.criar_container_reel,
            ("job-teste",),
            oauth.InstagramOAuthClientError,
            id="oauth-criar-container"
        ),
        pytest.param(
            oauth.consultar_reel,
            ("job-teste",),
            oauth.InstagramOAuthClientError,
            id="oauth-consultar"
        ),
        pytest.param(
            oauth.publicar_reel_servidor,
            ("job-teste",),
            oauth.InstagramOAuthClientError,
            id="oauth-publicar"
        ),
    ]
)
def test_operacao_instagram_bloqueada(
    funcao, argumentos, excecao
):
    assert config.INSTAGRAM_ENABLED is False
    assert direto.INSTAGRAM_ENABLED is False
    assert oauth.INSTAGRAM_ENABLED is False

    with (
        patch.object(
            direto.requests,
            "request",
            side_effect=AssertionError("Requisicao proibida")
        ) as rede_direta,
        patch.object(
            direto.requests,
            "post",
            side_effect=AssertionError("Upload proibido")
        ) as upload,
        patch.object(
            oauth,
            "urlopen",
            side_effect=AssertionError("Conexao proibida")
        ) as rede_oauth,
        patch.object(
            oauth,
            "_config",
            side_effect=AssertionError("Credenciais proibidas")
        ) as credenciais
    ):
        with pytest.raises(excecao) as erro:
            funcao(*argumentos)

        assert str(erro.value) == MENSAGEM

        rede_direta.assert_not_called()
        upload.assert_not_called()
        rede_oauth.assert_not_called()
        credenciais.assert_not_called()
