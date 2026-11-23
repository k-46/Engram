from pathlib import Path
from typing import Any, Iterable

import chromadb
from chromadb.config import Settings


class ChromaStore:
    def __init__(self, persist_directory: str | Path = "data/chroma", collection_name: str = "engram"):
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: Iterable[str],
        embeddings: Iterable[list[float]],
        documents: Iterable[str],
        metadatas: Iterable[dict[str, Any]],
    ) -> None:
        ids = list(ids)
        documents = list(documents)
        metadatas = list(metadatas)
        embeddings = [list(vector) for vector in embeddings]
        if not ids:
            return
        if not (len(ids) == len(documents) == len(metadatas) == len(embeddings)):
            raise ValueError("ids, embeddings, documents and metadatas must have equal lengths")
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, max(1, self.collection.count())),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def reset(self) -> None:
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self.collection.count()
