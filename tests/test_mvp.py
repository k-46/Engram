import tempfile

import numpy as np

from src.chunking.chunker import _document_text, chunk_text
from src.embeddings.embedder import Embedder
from src.ingestion.loader import load_corpus
from src.ingestion.processor import clean_text
from src.vector_store.chroma_store import ChromaStore
from src.pipeline import EngramPipeline


def test_corpus_loads_twelve_documents():
    documents = load_corpus("data/sample_corpus.json")
    assert len(documents) == 12
    assert len({document["document_id"] for document in documents}) == 12


def test_clean_text_normalizes_whitespace():
    assert clean_text("  Hello\r\n\r\nworld  \t text ") == "Hello\n\nworld text"


def test_chunking_has_overlap():
    assert chunk_text("one two three four five six", chunk_size=4, overlap=2) == [
        "one two three four",
        "three four five six",
    ]


def test_empty_chunking():
    assert chunk_text("   ") == []


def test_document_context_is_conversational():
    context = _document_text({
        "title": "Webhook outage",
        "detected_at": "2024-01-02",
        "root_cause": "A timeout in the provider",
    })
    assert "This document is about Webhook outage." in context
    assert "It was detected at 2024-01-02." in context


def test_embedding_dimensions_are_consistent():
    vectors = Embedder(dimensions=384).encode(["database timeout", "authentication"])
    assert isinstance(vectors, np.ndarray)
    assert vectors.shape == (2, 384)


def test_chroma_persistence_and_duplicate_upsert():
    directory = tempfile.mkdtemp(prefix="engram-test-")
    store = ChromaStore(directory)
    store.upsert(["d1"], [[1.0, 0.0]], ["test document"], [{"id": "d1"}])
    store.upsert(["d1"], [[1.0, 0.0]], ["test document"], [{"id": "d1"}])
    assert store.count() == 1


def test_pipeline_answers_database_query(tmp_path):
    pipeline = EngramPipeline(chroma_dir=tmp_path / "chroma", rebuild=True)
    result = pipeline.answer(
        "What database should the platform use for operational data?"
    )
    assert "PostgreSQL" in result["answer"]
    assert any(source.document_id == "ADR-001" for source in result["sources"])


def test_pipeline_handles_insufficient_context(tmp_path):
    pipeline = EngramPipeline(chroma_dir=tmp_path / "chroma", rebuild=True)
    result = pipeline.answer("Explain quantum teleportation requirements")
    assert "could not find enough relevant" in result["answer"].lower()


def test_pipeline_rejects_ambiguous_overview(tmp_path):
    pipeline = EngramPipeline(chroma_dir=tmp_path / "chroma", rebuild=True)
    result = pipeline.answer("Tell me about the system")
    assert "clarify" in result["answer"].lower()
    assert result["sources"] == []


def test_pipeline_persists_index(tmp_path):
    first = EngramPipeline(chroma_dir=tmp_path / "chroma", rebuild=True)
    assert first.store.count() == 12
    restarted = EngramPipeline(chroma_dir=tmp_path / "chroma")
    assert restarted.store.count() == 12
