import logging

from pathlib import Path

logger = logging.getLogger(__name__)

REPOSITORIOS_WHISPER = {
    "base": "Systran/faster-whisper-base",
}


def erro_de_arquivo_modelo(erro):
    """Identifica possiveis falhas nos arquivos do modelo."""
    mensagem = str(erro).lower()

    indicadores = (
        "unable to open file",
        "model.bin",
        "config.json",
        "tokenizer.json",
        "unable to read file",
    )

    return any(item in mensagem for item in indicadores)


def carregar_modelo_whisper(nome):
    """Carrega o modelo e tenta recupera-lo quando necessario."""

    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download

    parametros = {
        "device": "cpu",
        "compute_type": "int8",
        "cpu_threads": 2,
        "num_workers": 1,
    }

    try:
        return WhisperModel(nome, **parametros)

    except (RuntimeError, OSError, ValueError) as erro:

        if not erro_de_arquivo_modelo(erro):
            raise

        repositorio = REPOSITORIOS_WHISPER.get(nome)

        if repositorio is None:
            raise

        logger.warning(
            "Falha ao carregar Whisper %s: %s",
            nome,
            erro,
        )

        logger.info(
            "Iniciando recuperacao do modelo Whisper."
        )

        try:
            caminho = snapshot_download(
                repo_id=repositorio,
                force_download=True,
                allow_patterns=[
                    "config.json",
                    "model.bin",
                    "tokenizer.json",
                    "vocabulary.*",
                    "preprocessor_config.json",
                ],
                max_workers=2,
            )

            arquivo_modelo = Path(caminho) / "model.bin"

            if (
                not arquivo_modelo.is_file()
                or arquivo_modelo.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Arquivo model.bin ausente ou vazio."
                )

            modelo = WhisperModel(
                str(caminho),
                **parametros,
            )

            logger.info(
                "Modelo Whisper recuperado com sucesso."
            )

            return modelo

        except Exception as erro_recuperacao:

            logger.exception(
                "Falha na recuperacao do modelo Whisper."
            )

            raise RuntimeError(
                "N\u00e3o foi poss\u00edvel recuperar o modelo "
                "de intelig\u00eancia artificial das legendas. "
                "Verifique sua conex\u00e3o com a internet, "
                "o espa\u00e7o dispon\u00edvel em disco e "
                "tente novamente."
            ) from erro_recuperacao
