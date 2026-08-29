"""Indexação dos chunks SQLite no ChromaDB e busca semântica."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from .database import create_session_factory, session_scope
from .embeddings import EmbeddingService
from .models import Chunk
from .vector_store import ChromaStore


def _database_url(cfg: dict[str, Any]) -> str:
    root = Path(cfg["_root"])
    url = str(cfg["banco"]["url"])
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        return f"sqlite:///{root / url[len('sqlite:///'):]}"
    return url


def _load_chunks(cfg: dict[str, Any]) -> list[Chunk]:
    factory = create_session_factory(_database_url(cfg))
    with session_scope(factory) as session:
        return list(session.scalars(select(Chunk).order_by(Chunk.id)).all())


def _metadata_from_chunk(chunk: Chunk) -> dict[str, Any]:
    try:
        metadata = json.loads(chunk.metadata_json or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return metadata if isinstance(metadata, dict) else {}


def build_index(cfg: dict[str, Any]) -> int:
    """Sincroniza os chunks persistidos com a coleção Chroma sem duplicatas."""
    root = Path(cfg["_root"])
    chunks = [chunk for chunk in _load_chunks(cfg) if str(chunk.conteudo or "").strip()]
    store = ChromaStore(
        root / cfg["chromadb"]["diretorio"],
        cfg["chromadb"]["colecao"],
    )
    desired_ids = {str(chunk.id) for chunk in chunks}
    existing_ids = set(store.get().get("ids", []))
    stale = sorted(existing_ids - desired_ids)
    if stale:
        store.delete(stale)
    if not chunks:
        return 0

    documents = [str(chunk.conteudo).strip() for chunk in chunks]
    service = EmbeddingService(cfg["embeddings"]["modelo"])
    vectors = service.encode(documents)
    if vectors.shape[0] != len(chunks):
        raise RuntimeError("Quantidade de embeddings divergente da quantidade de chunks")
    store.upsert(
        ids=[str(chunk.id) for chunk in chunks],
        documents=documents,
        metadatas=[_metadata_from_chunk(chunk) for chunk in chunks],
        embeddings=vectors.tolist(),
    )
    return len(chunks)


def _build_where(category: str | None, protocol: str | None) -> dict[str, Any] | None:
    filters: list[dict[str, Any]] = []
    if category and category.strip():
        filters.append({"categoria": category.strip()})
    if protocol and protocol.strip():
        filters.append({"protocolo": protocol.strip()})
    if not filters:
        return None
    return filters[0] if len(filters) == 1 else {"$and": filters}


def semantic_query(
    cfg: dict[str, Any],
    question: str,
    top_k: int = 5,
    category: str | None = None,
    protocol: str | None = None,
) -> list[dict[str, Any]]:
    """Gera embedding da pergunta e retorna chunks com fonte e pontuação."""
    question = str(question or "").strip()
    if not question or top_k <= 0:
        return []

    root = Path(cfg["_root"])
    service = EmbeddingService(cfg["embeddings"]["modelo"])
    vector = service.encode([question])
    if vector.size == 0:
        return []
    store = ChromaStore(
        root / cfg["chromadb"]["diretorio"],
        cfg["chromadb"]["colecao"],
    )
    rows = store.query(
        embedding=vector[0].tolist(),
        top_k=top_k,
        where=_build_where(category, protocol),
    )
    results: list[dict[str, Any]] = []
    for row in rows:
        metadata = dict(row.get("metadata") or {})
        results.append(
            {
                **metadata,
                "id": row.get("id"),
                "conteudo": row.get("conteudo"),
                "distancia": row.get("distancia"),
                "similaridade": (
                    round(float(row["similaridade"]), 4)
                    if row.get("similaridade") is not None
                    else None
                ),
            }
        )
    return results
