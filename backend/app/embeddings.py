from __future__ import annotations

from sentence_transformers import SentenceTransformer

from .config import settings


class Embedder:
    """Lazy, reusable sentence-transformers embedder.

    The model is downloaded and cached on first use (sentencetransformers cache
    dir), so cold starts are slightly slower than warm ones.
    """

    _model: SentenceTransformer | None = None

    @classmethod
    def _get(cls) -> SentenceTransformer:
        if cls._model is None:
            cls._model = SentenceTransformer(settings.embed_model)
        return cls._model

    @classmethod
    def embed_text(cls, text: str) -> list[float]:
        return cls._get().encode([text], normalize_embeddings=True).tolist()[0]

    @classmethod
    def embed_chunks(cls, texts: list[str]) -> list[list[float]]:
        return cls._get().encode(texts, normalize_embeddings=True).tolist()
