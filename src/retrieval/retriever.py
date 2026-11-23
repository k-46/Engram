from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    document_id: str
    metadata: dict[str, Any]
    score: float


class Retriever:
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        query_vector = self.embedder.encode(query)[0].tolist()
        result = self.store.query(query_vector, top_k=top_k, where=where)
        ids = result["ids"][0] if result["ids"] else []
        documents = result["documents"][0] if result["documents"] else []
        metadatas = result["metadatas"][0] if result["metadatas"] else []
        distances = result["distances"][0] if result["distances"] else []
        output: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            metadata = dict(metadata or {})
            output.append(
                RetrievedChunk(
                    text=text,
                    document_id=str(metadata.get("id", chunk_id.split(":")[0])),
                    metadata=metadata,
                    score=1.0 - float(distance),
                )
            )
        return output
