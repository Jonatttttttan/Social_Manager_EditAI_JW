import json
import os
from pathlib import Path

from promptvideo.config import BASE

ARQUIVO_PRESETS = BASE / "presets.json"


def listar_presets():
    if not ARQUIVO_PRESETS.exists():
        return {}

    with ARQUIVO_PRESETS.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, dict):
        raise ValueError("O arquivo de presets possui formato inválido.")

    return dados


def salvar_preset(nome, configuracoes):
    nome = str(nome).strip()

    if not nome:
        raise ValueError("Informe um nome para o preset.")

    if len(nome) > 80:
        raise ValueError("O nome deve ter no máximo 80 caracteres.")

    if not isinstance(configuracoes, dict):
        raise ValueError("Configurações inválidas.")

    presets = listar_presets()
    presets[nome] = configuracoes

    ARQUIVO_PRESETS.parent.mkdir(parents=True, exist_ok=True)

    temporario = ARQUIVO_PRESETS.with_suffix(".tmp")

    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(presets, arquivo, ensure_ascii=False, indent=2)

    os.replace(temporario, ARQUIVO_PRESETS)

    return nome


def carregar_preset(nome):
    presets = listar_presets()

    if nome not in presets:
        raise ValueError("Preset não encontrado.")

    return presets[nome]


def excluir_preset(nome):
    presets = listar_presets()

    if nome not in presets:
        raise ValueError("Preset não encontrado.")

    del presets[nome]

    temporario = ARQUIVO_PRESETS.with_suffix(".tmp")

    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(presets, arquivo, ensure_ascii=False, indent=2)

    os.replace(temporario, ARQUIVO_PRESETS)
