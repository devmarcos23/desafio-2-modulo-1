"""Normalização linguística, tokenização e divisão de texto em chunks."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from typing import Any

STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "um", "uma",
    "para", "por", "com", "que", "no", "na", "nos", "nas", "ao", "aos", "à", "às",
}


def normalize_text(text: str) -> str:
    """Normaliza espaços e NUL sem apagar o texto original persistido."""
    return re.sub(r"\s+", " ", str(text or "").replace("\x00", " ")).strip()


def tokens(text: str) -> list[str]:
    """Tokeniza em minúsculas, remove acentos e stopwords básicas."""
    plain = (
        unicodedata.normalize("NFKD", str(text or "").lower())
        .encode("ascii", "ignore")
        .decode()
    )
    return [
        token
        for token in re.findall(r"[a-z0-9]+", plain)
        if token not in STOPWORDS
    ]


@lru_cache(maxsize=1)
def _stemmer():
    """Carrega o stemmer português do NLTK, que não exige download de corpus."""
    try:
        from nltk.stem.snowball import SnowballStemmer

        return SnowballStemmer("portuguese")
    except Exception:
        return None


def lemma_equivalent(token: str) -> str:
    """Aplica stemming como processo equivalente à lematização para o RF05."""
    stemmer = _stemmer()
    if stemmer is not None:
        return stemmer.stem(token)
    # fallback determinístico caso NLTK não esteja disponível
    for suffix in ("mente", "coes", "cao", "ando", "endo", "idos", "adas", "ado", "ida", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            return token[: -len(suffix)]
    return token


def preprocess(text: str) -> str:
    """Produz a versão limpa usada na recuperação sem alterar o texto bruto."""
    return " ".join(lemma_equivalent(token) for token in tokens(text))


def split_chunks(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    """Divide em chunks com sobreposição e preferência por fronteira de palavra."""
    text = normalize_text(text)
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Parâmetros de chunk inválidos")
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def metadata_json(**kwargs: Any) -> str:
    """Serializa metadados dos chunks de forma estável."""
    return json.dumps(kwargs, ensure_ascii=False, sort_keys=True)
