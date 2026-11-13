
import ctypes
import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from promptvideo.core.media import ffmpeg_bin


URL_EDITOR = "http://127.0.0.1:7860"
NOME_MUTEX = "Local\\EditAIVideosJW_SingleInstance_v0983"

_mutex_handle = None


def configurar_logs():
    base = Path(
        os.environ.get("LOCALAPPDATA")
        or (Path.home() / "AppData" / "Local")
    )

    pasta_logs = base / "EditAI Videos JW" / "logs"
    pasta_logs.mkdir(parents=True, exist_ok=True)

    arquivo_log = pasta_logs / "editor.log"

    if sys.stdout is None:
        sys.stdout = open(
            arquivo_log, "a", encoding="utf-8", buffering=1
        )

    if sys.stderr is None:
        sys.stderr = open(
            arquivo_log, "a", encoding="utf-8", buffering=1
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(arquivo_log, encoding="utf-8")
        ],
    )


def instancia_ja_existe():
    global _mutex_handle

    if os.name != "nt":
        return False

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.CreateMutexW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_wchar_p,
    ]
    kernel32.CreateMutexW.restype = ctypes.c_void_p

    _mutex_handle = kernel32.CreateMutexW(
        None,
        False,
        NOME_MUTEX,
    )

    if not _mutex_handle:
        raise OSError(
            ctypes.get_last_error(),
            "Nao foi possivel criar o mutex do EditAI",
        )

    return ctypes.get_last_error() == 183


def verificar_ffmpeg():
    flags = (
        subprocess.CREATE_NO_WINDOW
        if os.name == "nt"
        else 0
    )

    for binario in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run(
                [ffmpeg_bin(binario), "-version"],
                capture_output=True,
                check=True,
                creationflags=flags,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SystemExit(
                f"{binario} nao encontrado: {exc}"
            )


def main():
    configurar_logs()

    if instancia_ja_existe():
        logging.info(
            "Instancia existente detectada; reabrindo navegador."
        )
        webbrowser.open(URL_EDITOR)
        return

    verificar_ffmpeg()

    from promptvideo.licensing import startup_gate
    startup_gate()

    from promptvideo.ui.gradio_app import iniciar
    iniciar()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception(
            "Erro fatal ao iniciar o EditAI Videos JW"
        )
        raise
