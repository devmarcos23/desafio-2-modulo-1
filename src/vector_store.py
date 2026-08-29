"""Persistência e consulta de chunks no ChromaDB."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence


class ChromaStore:
    """Gerencia uma coleção persistente de embeddings no ChromaDB."""

    def __init__(
        self,
        directory: str | Path,
        collection: str,
    ) -> None:
        """
        Inicializa o banco vetorial.

        Args:
            directory: Diretório onde o ChromaDB será persistido.
            collection: Nome da coleção.

        Raises:
            ValueError: Caso diretório ou coleção sejam inválidos.
        """
        if not collection or not collection.strip():
            raise ValueError("O nome da coleção não pode ser vazio.")

        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        import chromadb

        self.directory = path
        self.collection_name = collection

        self.client = chromadb.PersistentClient(
            path=str(path)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        """Retorna a quantidade de itens armazenados na coleção."""
        return int(self.collection.count())

    def upsert(
        self,
        ids: Sequence[str],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """
        Insere ou atualiza documentos e seus embeddings.

        O método utiliza upsert, portanto registros com o mesmo ID
        são atualizados em vez de duplicados.

        Args:
            ids: Identificadores únicos dos chunks.
            documents: Textos dos chunks.
            metadatas: Metadados associados aos chunks.
            embeddings: Vetores dos chunks.

        Raises:
            ValueError: Caso as listas tenham tamanhos diferentes.
        """
        ids = list(ids)
        documents = list(documents)
        metadatas = list(metadatas)
        embeddings = [list(vector) for vector in embeddings]

        quantidade = len(ids)

        if quantidade == 0:
            return

        if len(documents) != quantidade:
            raise ValueError(
                "A quantidade de documentos deve ser igual à "
                "quantidade de IDs."
            )

        if len(metadatas) != quantidade:
            raise ValueError(
                "A quantidade de metadados deve ser igual à "
                "quantidade de IDs."
            )

        if len(embeddings) != quantidade:
            raise ValueError(
                "A quantidade de embeddings deve ser igual à "
                "quantidade de IDs."
            )

        if any(not str(item).strip() for item in ids):
            raise ValueError(
                "Todos os IDs dos chunks devem ser preenchidos."
            )

        if any(not isinstance(metadata, dict) for metadata in metadatas):
            raise ValueError(
                "Todos os metadados devem ser dicionários."
            )

        if any(len(vector) == 0 for vector in embeddings):
            raise ValueError(
                "Os embeddings não podem possuir vetores vazios."
            )

        self.collection.upsert(
            ids=[str(item) for item in ids],
            documents=[str(item) for item in documents],
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def query(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Consulta os chunks mais semelhantes a um embedding.

        Args:
            embedding: Vetor utilizado como consulta.
            top_k: Quantidade máxima de resultados.
            where: Filtro opcional de metadados.

        Returns:
            Lista de resultados contendo conteúdo, metadados,
            distância e similaridade.
        """
        if top_k <= 0:
            return []

        vector = list(embedding)

        if not vector:
            return []

        total = self.count

        if total == 0:
            return []

        quantidade = min(top_k, total)

        result = self.collection.query(
            query_embeddings=[vector],
            n_results=quantidade,
            where=where,
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]

        rows: list[dict[str, Any]] = []

        for index, document in enumerate(documents):
            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            distance = (
                float(distances[index])
                if index < len(distances)
                else None
            )

            chunk_id = (
                ids[index]
                if index < len(ids)
                else None
            )

            similarity = None

            if distance is not None:
                similarity = max(
                    0.0,
                    min(1.0, 1.0 - distance),
                )

            rows.append(
                {
                    "id": chunk_id,
                    "conteudo": document,
                    "metadata": metadata,
                    "distancia": distance,
                    "similaridade": similarity,
                }
            )

        return rows

    def delete(self, ids: Sequence[str]) -> None:
        """
        Remove chunks específicos da coleção.

        Args:
            ids: IDs dos chunks que deverão ser removidos.
        """
        ids = [str(item) for item in ids if str(item).strip()]

        if not ids:
            return

        self.collection.delete(ids=ids)

    def clear(self) -> None:
        """Remove todos os registros da coleção atual."""
        ids = self.collection.get().get("ids", [])

        if ids:
            self.collection.delete(ids=ids)

    def get(
        self,
        ids: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """
        Recupera registros armazenados.

        Args:
            ids: IDs específicos. Se omitido, recupera os registros
                disponíveis na coleção.

        Returns:
            Estrutura retornada pelo ChromaDB.
        """
        if ids is None:
            return self.collection.get()

        normalized_ids = [
            str(item)
            for item in ids
            if str(item).strip()
        ]

        if not normalized_ids:
            return {
                "ids": [],
                "documents": [],
                "metadatas": [],
            }

        return self.collection.get(ids=normalized_ids)