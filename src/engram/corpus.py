"""Loading and validating Engram's sample corpus."""

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from .models import Document, validate_corpus

DOCUMENT_ADAPTER = TypeAdapter(Document)


def load_corpus(path: str | Path) -> list[Document]:
    """Load a JSON array of documents and validate cross-document links."""

    raw_documents: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw_documents, list):
        raise ValueError("corpus must be a JSON array")
    documents = [DOCUMENT_ADAPTER.validate_python(item) for item in raw_documents]
    return validate_corpus(documents)
