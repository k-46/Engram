"""Load and validate Engram's complete corpus."""

from pathlib import Path

from .ingestion import load_documents
from .models import Document, validate_corpus


def load_corpus(path: str | Path) -> list[Document]:
    """Load a JSON array of documents and validate cross-document links."""

    documents = load_documents(path)
    return validate_corpus(documents)
