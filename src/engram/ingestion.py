"""Read and validate individual Engram documents from JSON."""

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from .models import Document

DOCUMENT_ADAPTER = TypeAdapter(Document)


class DocumentIngestionError(ValueError):
    """An error raised while reading or validating a document corpus."""

    def __init__(
        self,
        message: str,
        *,
        path: str | Path,
        document_index: int | None = None,
        document_id: str | None = None,
        document_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.path = Path(path)
        self.document_index = document_index
        self.document_id = document_id
        self.document_type = document_type


def load_documents(path: str | Path) -> list[Document]:
    """Read a JSON array and return its validated document objects.

    Per-document errors include the zero-based array index and any identifying
    fields available before Pydantic validation.
    """

    source_path = Path(path)
    try:
        raw_content = source_path.read_text(encoding="utf-8")
        raw_documents: Any = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise DocumentIngestionError(
            f"invalid JSON in {source_path}: {error.msg} "
            f"(line {error.lineno}, column {error.colno})",
            path=source_path,
        ) from error
    except OSError as error:
        raise DocumentIngestionError(
            f"could not read {source_path}: {error}",
            path=source_path,
        ) from error

    if not isinstance(raw_documents, list):
        raise DocumentIngestionError(
            f"corpus in {source_path} must be a JSON array",
            path=source_path,
        )

    documents: list[Document] = []
    for index, raw_document in enumerate(raw_documents):
        if not isinstance(raw_document, dict):
            raise DocumentIngestionError(
                f"document at index {index} in {source_path} must be a JSON object",
                path=source_path,
                document_index=index,
            )

        document_id = _string_field(raw_document, "document_id")
        document_type = _string_field(raw_document, "document_type")
        try:
            documents.append(DOCUMENT_ADAPTER.validate_python(raw_document))
        except ValidationError as error:
            identity = f"document at index {index}"
            if document_id is not None:
                identity += f" ({document_id})"
            if document_type is not None:
                identity += f" of type {document_type}"
            raise DocumentIngestionError(
                f"invalid {identity} in {source_path}: {error}",
                path=source_path,
                document_index=index,
                document_id=document_id,
                document_type=document_type,
            ) from error

    return documents


def _string_field(document: dict[str, Any], field_name: str) -> str | None:
    value = document.get(field_name)
    return value if isinstance(value, str) else None
