import json
from pathlib import Path
from typing import Any


def load_corpus(path: str | Path) -> list[dict[str, Any]]:
    corpus_path = Path(path)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    with corpus_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("Corpus JSON must contain a list of documents")
    return data


def load_validated_corpus(path: str | Path) -> list[dict[str, Any]]:
    """Load Engram's typed corpus and return serializable document mappings."""
    try:
        from engram.corpus import load_corpus as load_engram_corpus
    except ModuleNotFoundError:
        from src.engram.corpus import load_corpus as load_engram_corpus

    return [document.model_dump(mode="json") for document in load_engram_corpus(path)]
