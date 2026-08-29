"""Normalização linguística e divisão de texto em chunks."""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

STOPWORDS = {
    "a",
    "o",
    "as",
    "os",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "em",
    "um",
    "uma",
    "para",
    "por",
    "com",
    "que",
    "no",
    "na",
}


def normalize_text(text: str) -> str:
    """Remove NUL e normaliza espaços sem alterar o conteúdo semântico."""
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def tokens(text: str) -> list[str]:
    """Tokeniza em minúsculas, remove acentos e stopwords básicas."""
    plain = (
        unicodedata.normalize("NFKD", text.lower())
        .encode("ascii", "ignore")
        .decode()
    )
    return [
        token
        for token in re.findall(r"[a-z0-9]+", plain)
        if token not in STOPWORDS
    ]


def lemma_light(token: str) -> str:
    """Aplica redução morfológica leve, sem exigir corpus/modelo externo.

    Trata-se de um processo equivalente simplificado para o escopo didático,
    evitando downloads adicionais durante a instalação local.
    """
    suffixes = (
        "mente",
        "coes",
        "cao",
        "ando",
        "endo",
        "idos",
        "adas",
        "ado",
        "ida",
        "s",
    )
    for suffix in suffixes:
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            return token[: -len(suffix)]
    return token


def preprocess(text: str) -> str:
    """Produz a versão usada na recuperação, preservando o original fora daqui."""
    return " ".join(lemma_light(token) for token in tokens(text))


def split_chunks(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    """Divide texto por caracteres, preferindo fronteiras de palavra.

    A sobreposição reduz perda de contexto entre chunks adjacentes.
    """
    text = normalize_text(text)
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Parâmetros de chunk inválidos")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap

    return [chunk for chunk in chunks if chunk]


def metadata_json(**kwargs: Any) -> str:
    """Serializa metadados de chunks de forma estável e legível."""
    return json.dumps(kwargs, ensure_ascii=False, sort_keys=True)
