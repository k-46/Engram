from dataclasses import dataclass
from typing import Iterable

from src.ingestion.processor import clean_text


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks


def chunk_documents(documents: Iterable[dict], chunk_size: int = 500, overlap: int = 100) -> list[Chunk]:
    output: list[Chunk] = []
    for document in documents:
        document_id = str(document.get("document_id", document.get("id", ""))).strip()
        if not document_id:
            continue
        text = clean_text(str(document.get("text", ""))) or _document_text(document)
        if not text:
            continue
        metadata = dict(document)
        metadata.pop("text", None)
        metadata["id"] = document_id
        metadata.update(document.get("metadata", {}))
        for index, chunk in enumerate(chunk_text(text, chunk_size, overlap)):
            output.append(Chunk(
                chunk_id=f"{document_id}:chunk:{index}",
                document_id=document_id,
                text=chunk,
                metadata=metadata,
            ))
    return output


def _document_text(document: dict) -> str:
    excluded = {"document_id", "title", "document_type", "document_date", "status",
                "related_documents", "relationships", "text", "metadata"}
    sections = [f"This document is about {document.get('title', '')}."]
    for key, value in document.items():
        if key in excluded or value in (None, "", []):
            continue
        if isinstance(value, list):
            value = "; ".join(item if isinstance(item, str) else str(item) for item in value)
        sections.append(_friendly_sentence(key, value))
    return "\n".join(sections)


def _friendly_sentence(key: str, value: object) -> str:
    phrases = {
        "detected_at": "It was detected at",
        "resolved_at": "It was resolved at",
        "document_date": "It was documented on",
        "context": "The context was",
        "decision": "The decision was",
        "impact": "The impact was",
        "root_cause": "The root cause was",
        "resolution": "The resolution was",
        "problem_statement": "The problem was",
        "architecture": "The architecture uses",
        "rationale": "The reasoning was",
    }
    prefix = phrases.get(key, f"The {key.replace('_', ' ')} was")
    if prefix == "The problem was" and str(value).startswith("The "):
        value = str(value)[4:]
    return f"{prefix} {value}."
