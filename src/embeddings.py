"""Geração de embeddings e similaridade de cosseno."""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    """Carrega e reutiliza modelos SentenceTransformer no mesmo processo."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingService:
    """Serviço de embeddings baseado em ``sentence-transformers``."""

    def __init__(self, model_name: str) -> None:
        if not model_name or not model_name.strip():
            raise ValueError("O nome do modelo de embeddings não pode ser vazio")
        self.model_name = model_name.strip()
        self.model = _load_model(self.model_name)

    def encode(self, texts: Sequence[str], batch_size: int = 32) -> FloatArray:
        """Codifica textos em vetores normalizados."""
        if batch_size <= 0:
            raise ValueError("batch_size deve ser maior que zero")
        if not texts:
            return np.empty((0, 0), dtype=np.float64)
        normalized = [str(text or "").strip() for text in texts]
        if not any(normalized):
            return np.empty((len(normalized), 0), dtype=np.float64)
        vectors = self.model.encode(
            normalized,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float64)


def cosine_scores(query_vector: np.ndarray, matrix: np.ndarray) -> FloatArray:
    """Calcula a similaridade de cosseno da consulta contra uma matriz."""
    query = np.asarray(query_vector, dtype=np.float64).reshape(-1)
    data = np.asarray(matrix, dtype=np.float64)
    if query.size == 0 or data.size == 0:
        return np.empty(0, dtype=np.float64)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.ndim != 2 or data.shape[1] != query.shape[0]:
        raise ValueError("Dimensões incompatíveis para similaridade de cosseno")
    query_norm = np.linalg.norm(query)
    data_norms = np.linalg.norm(data, axis=1)
    denominator = data_norms * query_norm
    scores = np.zeros(data.shape[0], dtype=np.float64)
    valid = denominator > 0
    if np.any(valid):
        scores[valid] = (data[valid] @ query) / denominator[valid]
    return scores


def top_k(
    query: str,
    texts: Sequence[str],
    service: EmbeddingService,
    k: int = 5,
) -> list[tuple[int, float]]:
    """Retorna índices/pontuações dos textos mais próximos da consulta."""
    if k <= 0 or not str(query or "").strip() or not texts:
        return []
    vectors = service.encode([query, *[str(text or "") for text in texts]])
    if vectors.shape[0] <= 1:
        return []
    scores = cosine_scores(vectors[0], vectors[1:])
    indices = np.argsort(scores)[::-1][: min(k, len(scores))]
    return [(int(index), float(scores[index])) for index in indices]
