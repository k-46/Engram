import hashlib
import math
import os
import warnings
from typing import Iterable

import numpy as np
from dotenv import load_dotenv


class Embedder:
    """Semantic embeddings with a deterministic local fallback."""

    def __init__(self, model_name: str | None = None, dimensions: int = 384):
        load_dotenv()
        os.environ.setdefault("HF_HOME", "data/huggingface")
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", "data/huggingface/hub")
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.dimensions = dimensions
        self._model = None
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            if hasattr(self._model, "get_embedding_dimension"):
                self.dimensions = int(self._model.get_embedding_dimension())
            else:
                self.dimensions = int(self._model.get_sentence_embedding_dimension())
        except (ImportError, OSError, RuntimeError) as error:
            warnings.warn(
                f"Semantic embedding model '{self.model_name}' could not be loaded; "
                f"using the deterministic fallback ({error}).",
                RuntimeWarning,
                stacklevel=2,
            )

    @property
    def is_fallback(self) -> bool:
        return self._model is None

    def encode(self, texts: str | Iterable[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        texts = list(texts)
        if not texts:
            return np.empty((0, self.dimensions), dtype=np.float32)
        if self._model is not None:
            vectors = self._model.encode(texts, normalize_embeddings=True)
            return np.asarray(vectors, dtype=np.float32)
        result = np.asarray([self._hash_embed(text) for text in texts], dtype=np.float32)
        norms = np.linalg.norm(result, axis=1, keepdims=True)
        return result / np.maximum(norms, 1e-12)

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector
