
"""
EditAI Videos JW + Social Manager JW
Integração Instagram Reels - Meta Graph API.

Fluxo:
1. Validar vídeo e credenciais.
2. Criar contêiner de Reel.
3. Enviar MP4 para a Meta.
4. Consultar processamento.
5. Publicar após confirmação explícita.

O token é utilizado apenas em memória.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from promptvideo.config import INSTAGRAM_ENABLED


GRAPH_VERSION = "v24.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


class InstagramPublishError(RuntimeError):
    """Erro controlado da integração Instagram."""
    pass


def _request_json(method, url, token, **kwargs):
    """Executa requisições autenticadas à Graph API."""

    _garantir_instagram_habilitado()
    try:
        response = requests.request(
            method,
            url,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=60,
            **kwargs
        )

        data = response.json()

    except (requests.RequestException, ValueError) as exc:
        raise InstagramPublishError(
            "Não foi possível comunicar com a API da Meta."
        ) from exc

    if (
        not response.ok
        or not isinstance(data, dict)
        or data.get("error")
    ):
        error = (
            data.get("error", {})
            if isinstance(data, dict)
            else {}
        )

        if not isinstance(error, dict):
            error = {}

        mensagem = error.get(
            "message",
            "Requisição recusada pela Meta."
        )

        raise InstagramPublishError(
            f"Meta HTTP {response.status_code}: {mensagem}"
        )

    return data


def _validate(video, account_id, token):
    """Valida vídeo, conta e token."""

    video = Path(video)

    if not video.is_file():
        raise InstagramPublishError(
            "O arquivo de vídeo não foi encontrado."
        )

    if video.suffix.lower() != ".mp4":
        raise InstagramPublishError(
            "Selecione um vídeo MP4 exportado pelo editor."
        )

    if not account_id or not str(account_id).isdigit():
        raise InstagramPublishError(
            "Informe um ID numérico de conta Instagram válido."
        )

    if not token or not token.strip():
        raise InstagramPublishError(
            "Informe o token de teste da Meta."
        )

    return video


def _sanitizar_mensagem(mensagem, token):
    """
    Oculta algumas informações sensíveis
    de mensagens retornadas pela Meta.

    A sanitização é parcial: revisar antes
    de compartilhar qualquer saída.
    """

    mensagem = str(mensagem)

    if token:
        mensagem = mensagem.replace(token, "[TOKEN_OCULTO]")

    mensagem = re.sub(
        r"https?://[^\s\"']+",
        "[URL_OCULTA]",
        mensagem
    )

    mensagem = re.sub(
        r"(?i)(access_token|authorization)\s*[:=]\s*\S+",
        r"\1=[OCULTO]",
        mensagem
    )

    return mensagem[:500]


def preparar_reel(video, account_id, token, caption=""):
    """
    Cria o contêiner e envia o MP4.

    Esta função NÃO publica o Reel.

    Retorna o ID do contêiner.
    """

    _garantir_instagram_habilitado()
    video = _validate(video, account_id, token)

    # 1. Criar contêiner
    data = _request_json(
        "POST",
        f"{GRAPH_BASE}/{account_id}/media",
        token,
        data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption or "",
            "share_to_feed": "false"
        }
    )

    container_id = data.get("id")
    upload_url = data.get("uri")

    if not container_id or not upload_url:
        raise InstagramPublishError(
            "A Meta não retornou um contêiner válido."
        )

    # 2. Validar destino de upload
    destino = urlparse(upload_url)

    if (
        destino.scheme != "https"
        or destino.hostname != "rupload.facebook.com"
        or destino.username is not None
        or destino.password is not None
        or destino.port not in (None, 443)
    ):
        raise InstagramPublishError(
            "A Meta retornou um destino de upload inesperado."
        )

    # 3. Enviar MP4
    try:
        tamanho = video.stat().st_size

        with video.open("rb") as source:
            response = requests.post(
                upload_url,
                headers={
                    "Authorization": f"OAuth {token}",
                    "offset": "0",
                    "file_size": str(tamanho),
                    "Content-Type": "application/octet-stream"
                },
                data=source,
                timeout=300
            )

    except requests.RequestException as exc:
        raise InstagramPublishError(
            "Falha de conexão durante o upload. "
            f"Tipo: {type(exc).__name__}"
        ) from exc

    # 4. Diagnóstico do upload
    if not response.ok:
        try:
            dados = response.json()
        except ValueError:
            dados = None

        if isinstance(dados, dict):
            debug_info = dados.get("debug_info")

            if isinstance(debug_info, dict):
                tipo = debug_info.get(
                    "type", "desconhecido"
                )

                pode_tentar = debug_info.get(
                    "retriable", False
                )

                mensagem_debug = debug_info.get(
                    "message", "Sem detalhes"
                )

                mensagem_segura = _sanitizar_mensagem(
                    mensagem_debug,
                    token
                )

                print(
                    "[INSTAGRAM] Upload HTTP:",
                    response.status_code
                )

                print(
                    "[INSTAGRAM] Tipo do erro:",
                    tipo
                )

                print(
                    "[INSTAGRAM] Repetível:",
                    pode_tentar
                )

                print(
                    "[INSTAGRAM] Mensagem técnica:",
                    mensagem_segura
                )

                raise InstagramPublishError(
                    f"Upload HTTP {response.status_code}. "
                    f"Tipo: {tipo}. "
                    "Consulte o diagnóstico no terminal."
                )

            # Outros formatos JSON
            campos = [
                f"{chave}: {type(valor).__name__}"
                for chave, valor in dados.items()
            ]

            diagnostico = ", ".join(campos)

            if not diagnostico:
                diagnostico = "Objeto JSON vazio"

        elif isinstance(dados, list):
            diagnostico = (
                f"Lista com {len(dados)} elementos"
            )

        elif dados is None:
            diagnostico = "Resposta não é JSON válido"

        else:
            diagnostico = (
                f"Tipo: {type(dados).__name__}"
            )

        raise InstagramPublishError(
            f"Upload HTTP {response.status_code}. "
            f"Estrutura da resposta: {diagnostico}"
        )

    return container_id


def status_reel(container_id, token):
    """
    Consulta o processamento do Reel.

    Possíveis estados:
    IN_PROGRESS, FINISHED, ERROR, EXPIRED.
    """

    _garantir_instagram_habilitado()
    if not container_id:
        raise InstagramPublishError(
            "ID do contêiner não informado."
        )

    dados = _request_json(
        "GET",
        f"{GRAPH_BASE}/{container_id}",
        token,
        params={
            "fields": "status_code,status"
        }
    )

    estado = dados.get("status_code")
    if estado not in ("IN_PROGRESS", "FINISHED", "ERROR", "EXPIRED", "PUBLISHED"):
        raise InstagramPublishError("A Meta retornou um status de processamento inesperado.")
    return estado


def publicar_reel(account_id, container_id, token):
    """
    Publica um Reel preparado.

    ATENÇÃO:
    Esta função realiza uma publicação real.
    Deve ser chamada somente após confirmação
    explícita na interface do EditAI.
    """

    _garantir_instagram_habilitado()
    if not container_id:
        raise InstagramPublishError(
            "Prepare o Reel antes de publicar."
        )

    if not account_id or not str(account_id).isdigit():
        raise InstagramPublishError(
            "ID da conta Instagram inválido."
        )

    if not token or not token.strip():
        raise InstagramPublishError(
            "Token da Meta não informado."
        )

    # 1. Consultar processamento
    status = status_reel(
        container_id,
        token
    )

    if status != "FINISHED":
        raise InstagramPublishError(
            "O vídeo ainda não está pronto. "
            f"Status atual: {status}. "
            "Aguarde e tente novamente."
        )

    # 2. Publicar Reel
    dados = _request_json(
        "POST",
        f"{GRAPH_BASE}/{account_id}/media_publish",
        token,
        data={
            "creation_id": container_id
        }
    )

    media_id = dados.get("id")

    if not media_id:
        raise InstagramPublishError(
            "A Meta não retornou o ID da publicação. "
            "Verifique o Instagram antes de tentar novamente."
        )

    return media_id

def _garantir_instagram_habilitado():
    if not INSTAGRAM_ENABLED:
        raise InstagramPublishError(
            "A integra\u00e7\u00e3o com o Instagram est\u00e1 desativada nesta vers\u00e3o do EditAI."
        )
