"""Indexação e busca semântica dos chunks persistidos no ChromaDB."""

from __future__ import annotations

from pathlib import Path
import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .models import Chunk
from .embeddings import EmbeddingService
from .vector_store import ChromaStore


def _database_url(cfg: dict) -> str:
    """Resolve a URL do SQLite a partir da raiz do projeto."""

    root = Path(cfg["_root"])
    url = cfg["banco"]["url"]

    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        return "sqlite:///" + str(root / url[10:])

    return url


def build_index(cfg: dict) -> int:
    """
    Sincroniza todos os chunks do SQLite com o ChromaDB.

    O SQLite é a fonte oficial dos dados.
    """

    root = Path(cfg["_root"])
    url = _database_url(cfg)

    engine = create_engine(url)

    with Session(engine) as session:
        chunks = list(
            session.scalars(
                select(Chunk).order_by(Chunk.id)
            ).all()
        )

    store = ChromaStore(
        root / cfg["chromadb"]["diretorio"],
        cfg["chromadb"]["colecao"],
    )

    # ---------------------------------------------------------
    # Banco vazio
    # ---------------------------------------------------------

    if not chunks:
        store.sync(
            ids=[],
            documents=[],
            metadatas=[],
            embeddings=[],
        )

        return 0

    # ---------------------------------------------------------
    # Geração dos embeddings
    # ---------------------------------------------------------

    service = EmbeddingService(
        cfg["embeddings"]["modelo"]
    )

    documents = [
        chunk.conteudo
        for chunk in chunks
    ]

    vectors = service.encode(documents)

    # ---------------------------------------------------------
    # Metadados
    # ---------------------------------------------------------

    metadatas = [
        json.loads(chunk.metadata_json)
        for chunk in chunks
    ]

    ids = [
        str(chunk.id)
        for chunk in chunks
    ]

    # ---------------------------------------------------------
    # Sincronização
    # ---------------------------------------------------------

    store.sync(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=vectors.tolist(),
    )

    return len(chunks)


def semantic_query(
    cfg: dict,
    question: str,
    top_k: int = 5,
    category: str | None = None,
) -> list[dict]:
    """
    Executa busca semântica.

    Retorna no máximo um resultado por protocolo.
    """

    if top_k < 1:
        raise ValueError(
            "top_k deve ser maior ou igual a 1"
        )

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

    where = (
        {"categoria": category}
        if category
        else None
    )

    # Buscamos candidatos extras porque vários chunks
    # podem pertencer ao mesmo protocolo.
    candidate_k = max(
        top_k * 5,
        20,
    )

    # Evita pedir mais resultados do que existem.
    total = store.collection.count()

    if total == 0:
        return []

    candidate_k = min(
        candidate_k,
        total,
    )

    rows = store.query(
        embedding=query_vector,
        top_k=candidate_k,
        where=where,
    )

    # ---------------------------------------------------------
    # Remove duplicidades por protocolo
    # ---------------------------------------------------------

    best_by_protocol: dict[str, dict] = {}

    for row in rows:
        metadata = row.get("metadata") or {}

        protocolo = metadata.get("protocolo")

        if not protocolo:
            protocolo = (
                f"{metadata.get('documento', '')}:"
                f"{metadata.get('pagina', '')}:"
                f"{len(best_by_protocol)}"
            )

        resultado = {
            **metadata,
            "conteudo": row["conteudo"],
            "similaridade": round(
                float(row["similaridade"]),
                4,
            ),
        }

        existente = best_by_protocol.get(
            protocolo
        )

        if (
            existente is None
            or resultado["similaridade"]
            > existente["similaridade"]
        ):
            best_by_protocol[protocolo] = resultado

    # ---------------------------------------------------------
    # Ordenação
    # ---------------------------------------------------------

    resultados = sorted(
        best_by_protocol.values(),
        key=lambda item: item["similaridade"],
        reverse=True,
    )

    return resultados[:top_k]