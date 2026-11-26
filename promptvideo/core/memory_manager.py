import ctypes
import os
import math

from ctypes import wintypes


class MEMORYSTATUSEX(ctypes.Structure):

    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
    ]


def consultar_memoria():
    """Consulta a memoria fisica do Windows."""

    if os.name != "nt":
        return None

    try:
        kernel32 = ctypes.WinDLL(
            "kernel32",
            use_last_error=True
        )

        consultar = kernel32.GlobalMemoryStatusEx

        consultar.argtypes = [
            ctypes.POINTER(MEMORYSTATUSEX)
        ]

        consultar.restype = wintypes.BOOL

        memoria = MEMORYSTATUSEX()

        memoria.dwLength = ctypes.sizeof(memoria)

        if not consultar(ctypes.byref(memoria)):
            return None

        return {
            "ram_total_gb": (
                memoria.ullTotalPhys / 1024**3
            ),
            "ram_disponivel_gb": (
                memoria.ullAvailPhys / 1024**3
            ),
            "ram_utilizada_percentual": (
                memoria.dwMemoryLoad
            )
        }

    except Exception:
        return None


def deve_liberar_whisper(memoria=None):
    """Determina se o modelo deve sair do cache."""

    if memoria is None:
        memoria = consultar_memoria()

    if memoria is None:
        return True, "Memoria desconhecida"

    try:
        total = float(memoria["ram_total_gb"])
        disponivel = float(
            memoria["ram_disponivel_gb"]
        )

        if (
            not math.isfinite(total)
            or not math.isfinite(disponivel)
            or total <= 0
            or disponivel < 0
            or disponivel > total
        ):
            return True, "Dados de memoria invalidos"

        if total <= 8.5:
            return True, "Perfil de economia de RAM"

        limite = max(2.0, total * 0.20)

        if disponivel < limite:
            return True, "Memoria disponivel reduzida"

        return False, "Memoria suficiente para cache"

    except (KeyError, TypeError, ValueError, OverflowError):
        return True, "Dados de memoria inconclusivos"
