"""Serviço de geração de embeddings e busca por similaridade de cosseno."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


class EmbeddingService:
    """Responsável pela geração de embeddings utilizando Sentence Transformers."""

    def __init__(self, model_name: str) -> None:
        """
        Inicializa o modelo de embeddings.

        Args:
            model_name: Nome do modelo Sentence Transformer.
        """
        if not model_name or not model_name.strip():
            raise ValueError("O nome do modelo de embeddings não pode ser vazio.")

        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(
        self,
        texts: Sequence[str],
        batch_size: int = 32,
    ) -> FloatArray:
        """
        Converte textos em vetores numéricos.

        Os embeddings são normalizados para facilitar o cálculo
        de similaridade por produto escalar/cosseno.

        Args:
            texts: Lista ou sequência de textos.
            batch_size: Quantidade de textos processados por lote.

        Returns:
            Matriz NumPy contendo os embeddings normalizados.

        Raises:
            ValueError: Caso os textos sejam inválidos ou batch_size seja inválido.
        """
        if batch_size <= 0:
            raise ValueError("batch_size deve ser maior que zero.")

        if not texts:
            return np.empty((0, 0), dtype=np.float64)

        normalized_texts = [
            str(text).strip() if text is not None else ""
            for text in texts
        ]

        if not any(normalized_texts):
            return np.empty((len(normalized_texts), 0), dtype=np.float64)

        vectors = self.model.encode(
            normalized_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(vectors, dtype=np.float64)


def cosine_scores(
    query_vector: np.ndarray,
    matrix: np.ndarray,
) -> FloatArray:
    """
    Calcula a similaridade de cosseno entre uma consulta e vários vetores.

    Como os embeddings são normalizados pelo serviço, o produto escalar
    também representa a similaridade de cosseno.

    Args:
        query_vector: Vetor da consulta.
        matrix: Matriz contendo os vetores dos documentos.

    Returns:
        Array contendo uma pontuação para cada vetor da matriz.
    """
    query = np.asarray(query_vector, dtype=np.float64).reshape(-1)
    data = np.asarray(matrix, dtype=np.float64)

    if query.size == 0 or data.size == 0:
        return np.empty(0, dtype=np.float64)

    if data.ndim == 1:
        data = data.reshape(1, -1)

    if data.ndim != 2:
        raise ValueError("A matriz de embeddings deve possuir duas dimensões.")

    if data.shape[1] != query.shape[0]:
        raise ValueError(
            "A dimensão do vetor da consulta não corresponde "
            "à dimensão dos vetores da matriz."
        )

    query_norm = np.linalg.norm(query, axis=0)
    data_norms = np.linalg.norm(data, axis=1)

    denominador = data_norms * query_norm

    scores = np.zeros(data.shape[0], dtype=np.float64)

    valid = denominador > 0

    if np.any(valid):
        scores[valid] = (
            data[valid] @ query
        ) / denominador[valid]

    return scores


def top_k(
    query: str,
    texts: Sequence[str],
    service: EmbeddingService,
    k: int = 5,
) -> list[tuple[int, float]]:
    """
    Retorna os textos mais semelhantes à consulta.

    Args:
        query: Pergunta ou texto utilizado como consulta.
        texts: Textos que serão comparados.
        service: Serviço responsável pelos embeddings.
        k: Quantidade máxima de resultados.

    Returns:
        Lista de tuplas contendo:
        (índice do texto, pontuação de similaridade).
    """
    if k <= 0:
        return []

    if not query or not query.strip():
        return []

    if not texts:
        return []

    valid_texts = [
        str(text).strip() if text is not None else ""
        for text in texts
    ]

    vectors = service.encode([query, *valid_texts])

    if vectors.shape[0] <= 1:
        return []

    query_vector = vectors[0]
    document_vectors = vectors[1:]

    scores = cosine_scores(
        query_vector,
        document_vectors,
    )

    if scores.size == 0:
        return []

    limit = min(k, len(scores))

    indices = np.argsort(scores)[::-1][:limit]

    return [
        (int(index), float(scores[index]))
        for index in indices
    ]