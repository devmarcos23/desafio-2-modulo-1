"""Carregamento e validação centralizada das configurações do projeto."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_SECTIONS = {
    "entrada": ("diretorio_pdfs", "padrao"),
    "saida": ("diretorio", "csv", "indicadores", "log", "graficos"),
    "banco": ("url",),
    "ocr": ("idioma", "dpi", "min_caracteres_extracao_direta"),
    "embeddings": ("modelo", "tamanho_chunk", "sobreposicao"),
    "chromadb": ("diretorio", "colecao"),
    "api": ("cep_base_url", "timeout_segundos"),
    "rag": ("top_k", "modo_sem_chave"),
}


class ConfigError(RuntimeError):
    """Erro de configuração que impede uma inicialização previsível."""


def _validate_config(cfg: dict[str, Any]) -> None:
    """Valida a presença e alguns limites básicos do ``config.json``."""
    missing: list[str] = []
    for section, keys in _REQUIRED_SECTIONS.items():
        value = cfg.get(section)
        if not isinstance(value, dict):
            missing.append(section)
            continue
        for key in keys:
            if key not in value:
                missing.append(f"{section}.{key}")

    if missing:
        raise ConfigError(
            "Configuração incompleta. Campos ausentes: " + ", ".join(missing)
        )

    dpi = cfg["ocr"]["dpi"]
    min_chars = cfg["ocr"]["min_caracteres_extracao_direta"]
    chunk_size = cfg["embeddings"]["tamanho_chunk"]
    overlap = cfg["embeddings"]["sobreposicao"]

    if not isinstance(dpi, int) or dpi <= 0:
        raise ConfigError("ocr.dpi deve ser um inteiro positivo")
    if not isinstance(min_chars, int) or min_chars < 0:
        raise ConfigError(
            "ocr.min_caracteres_extracao_direta deve ser um inteiro >= 0"
        )
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ConfigError("embeddings.tamanho_chunk deve ser um inteiro positivo")
    if not isinstance(overlap, int) or overlap < 0 or overlap >= chunk_size:
        raise ConfigError(
            "embeddings.sobreposicao deve ser >= 0 e menor que tamanho_chunk"
        )


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Carrega ``config.json`` e as variáveis do arquivo ``.env``.

    O arquivo ``.env`` é opcional e é carregado sem sobrescrever variáveis já
    definidas no ambiente. O caminho do projeto é acrescentado em ``_root``
    para que os demais módulos resolvam caminhos relativos de forma portátil.
    """
    load_dotenv(ROOT / ".env", override=False)

    target = Path(path).expanduser() if path is not None else ROOT / "config.json"
    if not target.is_absolute():
        target = ROOT / target

    if not target.is_file():
        raise ConfigError(f"Arquivo de configuração não encontrado: {target}")

    try:
        with target.open(encoding="utf-8") as stream:
            cfg = json.load(stream)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"JSON de configuração inválido: {target}") from exc
    except OSError as exc:
        raise ConfigError(f"Não foi possível ler a configuração: {target}") from exc

    if not isinstance(cfg, dict):
        raise ConfigError("A raiz do arquivo de configuração deve ser um objeto JSON")

    _validate_config(cfg)
    cfg["_root"] = str(ROOT)
    return cfg


def resolve(root: str | Path, relative: str | Path) -> Path:
    """Resolve um caminho relativo em relação à raiz do projeto."""
    path = Path(relative).expanduser()
    return path if path.is_absolute() else Path(root) / path
