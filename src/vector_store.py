"""Persistência e consulta dos chunks no ChromaDB."""

from __future__ import annotations

from pathlib import Path


class ChromaStore:
    def __init__(
        self,
        directory: str | Path,
        collection: str,
    ):
        import chromadb

        self.client = chromadb.PersistentClient(
            path=str(directory)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """Insere ou atualiza documentos no ChromaDB."""

        if not ids:
            return

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def sync(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """
        Sincroniza o ChromaDB com a fonte oficial.

        O SQLite é considerado a fonte oficial.
        Qualquer registro existente no Chroma que não
        esteja na lista de IDs recebida será removido.
        """

        # Primeiro atualiza/inclui os registros válidos.
        self.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        # Recupera todos os IDs atualmente existentes.
        existentes = self.collection.get(
            include=[]
        )

        chroma_ids = existentes.get("ids", [])

        ids_oficiais = set(ids)

        ids_remover = [
            item_id
            for item_id in chroma_ids
            if item_id not in ids_oficiais
        ]

        if ids_remover:
            self.collection.delete(
                ids=ids_remover
            )

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        """Executa busca semântica."""

        if top_k < 1:
            raise ValueError(
                "top_k deve ser maior ou igual a 1"
            )

        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
        )

        documents = result.get("documents") or [[]]
        metadatas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]

        rows = []

        for index, document in enumerate(documents[0]):
            metadata = (
                metadatas[0][index]
                if metadatas and metadatas[0]
                else {}
            )

            distance = (
                float(distances[0][index])
                if distances and distances[0]
                else 0.0
            )

            rows.append(
                {
                    "conteudo": document,
                    "metadata": metadata,
                    "distancia": distance,
                    "similaridade": 1 - distance,
                }
            )

        return rows