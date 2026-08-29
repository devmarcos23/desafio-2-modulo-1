"""Indexação dos chunks persistidos no ChromaDB."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .embeddings import EmbeddingService
from .models import Chunk
from .vector_store import ChromaStore


def _build_database_url(cfg: dict[str, Any]) -> str:
    """Monta a URL do banco SQLite de forma compatível com o projeto."""
    root = Path(cfg["_root"])
    url = str(cfg["banco"]["url"])

    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relative_path = url[len("sqlite:///") :]
        database_path = root / relative_path
        return f"sqlite:///{database_path}"

    return url


def _load_chunks(cfg: dict[str, Any]) -> list[Chunk]:
    """Carrega todos os chunks persistidos no banco."""
    database_url = _build_database_url(cfg)

    engine = create_engine(
        database_url,
        future=True,
    )

    try:
        with Session(engine) as session:
            return list(
                session.scalars(
                    select(Chunk).order_by(
                        Chunk.id
                    )
                ).all()
            )
    finally:
        engine.dispose()


def _metadata_from_chunk(chunk: Chunk) -> dict[str, Any]:
    """Converte os metadados persistidos do chunk para dicionário."""
    if not chunk.metadata_json:
        return {}

    try:
        metadata = json.loads(chunk.metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}

    if not isinstance(metadata, dict):
        return {}

    return metadata


def build_index(cfg: dict[str, Any]) -> int:
    """
    Gera embeddings dos chunks e persiste no ChromaDB.

    Os IDs utilizados são os IDs dos próprios chunks no SQLite.
    Isso torna a indexação idempotente: executar novamente não
    cria duplicatas no ChromaDB.

    Returns:
        Quantidade de chunks indexados.
    """
    root = Path(cfg["_root"])

    chunks = _load_chunks(cfg)

    if not chunks:
        return 0

    documents = [
        str(chunk.conteudo or "").strip()
        for chunk in chunks
    ]

    valid_items = [
        (chunk, document)
        for chunk, document in zip(chunks, documents)
        if document
    ]

    if not valid_items:
        return 0

    chunks = [item[0] for item in valid_items]
    documents = [item[1] for item in valid_items]

    service = EmbeddingService(
        cfg["embeddings"]["modelo"]
    )

    vectors = service.encode(
        documents
    )

    if vectors.shape[0] != len(chunks):
        raise RuntimeError(
            "A quantidade de embeddings gerados "
            "não corresponde à quantidade de chunks."
        )

    metadatas = [
        _metadata_from_chunk(chunk)
        for chunk in chunks
    ]

    ids = [
        str(chunk.id)
        for chunk in chunks
    ]

    store = ChromaStore(
        root / cfg["chromadb"]["diretorio"],
        cfg["chromadb"]["colecao"],
    )

    store.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=vectors.tolist(),
    )

    return len(chunks)


def semantic_query(
    cfg: dict[str, Any],
    question: str,
    top_k: int = 5,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """
    Realiza uma busca semântica no ChromaDB.

    Args:
        cfg: Configuração da aplicação.
        question: Pergunta utilizada na busca.
        top_k: Quantidade máxima de resultados.
        category: Filtro opcional por categoria.

    Returns:
        Lista dos chunks mais semelhantes.
    """
    if not question or not question.strip():
        return []

    if top_k <= 0:
        return []

    root = Path(cfg["_root"])

    service = EmbeddingService(
        cfg["embeddings"]["modelo"]
    )

    query_vector = service.encode(
        [question]
    )[0].tolist()

    store = ChromaStore(
        root / cfg["chromadb"]["diretorio"],
        cfg["chromadb"]["colecao"],
    )

    where = None

    if category and category.strip():
        where = {
            "categoria": category.strip()
        }

    rows = store.query(
        embedding=query_vector,
        top_k=top_k,
        where=where,
    )

    results: list[dict[str, Any]] = []

    for row in rows:
        metadata = dict(
            row.get("metadata") or {}
        )

        results.append(
            {
                **metadata,
                "id": row.get("id"),
                "conteudo": row.get("conteudo"),
                "distancia": row.get("distancia"),
                "similaridade": round(
                    float(row["similaridade"]),
                    4,
                )
                if row.get("similaridade") is not None
                else None,
            }
        )

    return results