"""Persistência e consulta de chunks no ChromaDB."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence


class ChromaStore:
    """Encapsula uma coleção persistente com distância de cosseno."""

    def __init__(self, directory: str | Path, collection: str) -> None:
        if not collection or not collection.strip():
            raise ValueError("O nome da coleção não pode ser vazio")
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        import chromadb

        self.directory = path
        self.collection_name = collection.strip()
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return int(self.collection.count())

    def upsert(
        self,
        ids: Sequence[str],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        ids = [str(item) for item in ids]
        documents = [str(item) for item in documents]
        metadatas = list(metadatas)
        embeddings = [list(vector) for vector in embeddings]
        quantity = len(ids)
        if quantity == 0:
            return
        if not (len(documents) == len(metadatas) == len(embeddings) == quantity):
            raise ValueError("IDs, documentos, metadados e embeddings devem ter o mesmo tamanho")
        if any(not item.strip() for item in ids):
            raise ValueError("IDs de chunks não podem ser vazios")
        if any(not vector for vector in embeddings):
            raise ValueError("Embeddings não podem ser vazios")
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def query(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not embedding or self.count == 0:
            return []
        result = self.collection.query(
            query_embeddings=[list(embedding)],
            n_results=min(top_k, self.count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        rows: list[dict[str, Any]] = []
        for index, document in enumerate(documents):
            distance = float(distances[index]) if index < len(distances) else None
            similarity = None if distance is None else max(0.0, min(1.0, 1.0 - distance))
            rows.append(
                {
                    "id": ids[index] if index < len(ids) else None,
                    "conteudo": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distancia": distance,
                    "similaridade": similarity,
                }
            )
        return rows

    def delete(self, ids: Sequence[str]) -> None:
        ids = [str(item) for item in ids if str(item).strip()]
        if ids:
            self.collection.delete(ids=ids)

    def clear(self) -> None:
        ids = self.collection.get().get("ids", [])
        if ids:
            self.collection.delete(ids=ids)

    def get(self, ids: Sequence[str] | None = None) -> dict[str, Any]:
        if ids is None:
            return self.collection.get(include=["documents", "metadatas"])
        normalized = [str(item) for item in ids if str(item).strip()]
        if not normalized:
            return {"ids": [], "documents": [], "metadatas": []}
        return self.collection.get(ids=normalized, include=["documents", "metadatas"])
