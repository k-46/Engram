import os
from pathlib import Path

from dotenv import load_dotenv

from src.chunking.chunker import chunk_documents
from src.embeddings.embedder import Embedder
from src.generation.generator import Generator
from src.ingestion.loader import load_validated_corpus
from src.retrieval.retriever import Retriever
from src.vector_store.chroma_store import ChromaStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EngramPipeline:
    MIN_RELEVANCE_SCORE = 0.18
    AMBIGUOUS_PATTERNS = (
        "tell me about the system",
        "describe the system",
        "overview",
        "what is this",
        "tell me about the last",
        "tell me about the most recent",
        "what is the latest",
        "what is the last recent",
        "latest update",
        "recent update",
        "let me know about the recent",
        "let me know about the latest",
        "let me know about the last",
    )
    SPECIFIC_PATTERNS = (
        "redis",
        "postgres",
        "database",
        "incident",
        "webhook",
        "authorization",
        "gatekeeper",
        "role update",
        "migration",
        "read replica",
        "cloudqueue",
    )

    def __init__(
        self,
        corpus_path: str | Path = PROJECT_ROOT / "data" / "sample_corpus.json",
        chroma_dir: str | Path | None = None,
        top_k: int = 5,
        rebuild: bool = False,
    ):
        load_dotenv(PROJECT_ROOT / ".env")
        self.embedder = Embedder()
        store_directory = (
            Path(chroma_dir)
            if chroma_dir is not None
            else PROJECT_ROOT / os.getenv("CHROMA_DIR", "data/chroma")
        )
        if not store_directory.is_absolute():
            store_directory = PROJECT_ROOT / store_directory
        self.store = ChromaStore(store_directory)
        self.retriever = Retriever(self.embedder, self.store)
        self.generator = Generator()
        self.top_k = top_k
        corpus_path = Path(corpus_path)
        self.corpus_path = (
            corpus_path if corpus_path.is_absolute() else PROJECT_ROOT / corpus_path
        )
        if rebuild:
            self.store.reset()
        if rebuild or self.store.count() == 0:
            self.index_corpus()

    def index_corpus(self) -> int:
        documents = load_validated_corpus(self.corpus_path)
        chunks = chunk_documents(documents)
        if not chunks:
            raise ValueError("Corpus contains no valid, non-empty documents")
        embeddings = self.embedder.encode([chunk.text for chunk in chunks])
        metadatas = [
            {
                key: value
                for key, value in chunk.metadata.items()
                if isinstance(value, (str, int, float, bool))
            }
            for chunk in chunks
        ]
        self.store.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings.tolist(),
            documents=[chunk.text for chunk in chunks],
            metadatas=metadatas,
        )
        return len(chunks)

    def answer(self, question: str, top_k: int | None = None):
        normalized_question = question.strip().lower()
        has_specific_subject = any(
            pattern in normalized_question for pattern in self.SPECIFIC_PATTERNS
        )
        is_ambiguous = any(
            pattern in normalized_question for pattern in self.AMBIGUOUS_PATTERNS
        )
        if is_ambiguous and not has_specific_subject:
            return {
                "answer": "I can help, but please clarify. Do you mean the latest incident, architecture decision, design update, or a particular document?",
                "sources": [],
            }

        chunks = self.retriever.retrieve(question, top_k or self.top_k)
        chunks = [
            chunk for chunk in chunks
            if chunk.score >= self.MIN_RELEVANCE_SCORE
        ]
        if self.embedder.is_fallback:
            terms = {term.lower() for term in question.split() if len(term) > 2}
            chunks = [
                chunk for chunk in chunks
                if any(term in chunk.text.lower() for term in terms)
            ]

        unique_chunks = []
        seen_documents = set()
        for chunk in chunks:
            if chunk.document_id not in seen_documents:
                seen_documents.add(chunk.document_id)
                unique_chunks.append(chunk)
            if len(unique_chunks) == 3:
                break
        return {
            "answer": self.generator.generate(question, unique_chunks),
            "sources": unique_chunks,
        }
