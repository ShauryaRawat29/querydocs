from __future__ import annotations

import os
import pickle
import re
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings


@dataclass
class DocChunk:
    doc_id: str
    chunk_index: int
    text: str
    meta: dict | None = None


class VectorStore:
    """Persistable FAISS index keyed by doc_id.

    Lightweight wrapper — stores embeddings + metadata and writes/loads them to
    disk so the service can restart without re-ingesting everything.
    """

    def __init__(self, model: SentenceTransformer) -> None:
        self.model = model
        self._index = None
        self._metas: list[DocChunk] = []

    def _import(self):
        import faiss

        return faiss

    def _ensure_index(self, dim: int) -> None:
        if self._index is not None:
            return
        faiss = self._import()
        self._index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))

    def add(self, chunks: list[DocChunk], embeddings: list[list[float]]) -> None:
        dim = len(embeddings[0])
        self._ensure_index(dim)
        vectors = np.array(embeddings, dtype="float32")
        self._index.add_with_ids(vectors, np.arange(len(self._metas), len(self._metas) + len(chunks)))
        for i, chunk in enumerate(chunks):
            self._metas.append(DocChunk(chunk.doc_id, chunk.chunk_index, chunk.text, chunk.meta))

    def search(self, query_vec: list[float], k: int = 5) -> list[DocChunk]:
        if self._index is None:
            return []
        self._import()
        k = min(k, len(self._metas))
        _dist, idxs = self._index.search(np.array([query_vec], dtype="float32"), k)
        return [self._metas[i] for i in idxs[0] if i != -1]

    def persist(self) -> None:
        if self._index is None:
            return
        os.makedirs(settings.index_path, exist_ok=True)
        faiss = self._import()
        faiss.write_index(self._index, os.path.join(settings.index_path, "index.faiss"))
        with open(os.path.join(settings.index_path, "meta.pkl"), "wb") as f:
            pickle.dump(self._metas, f)

    def load(self) -> bool:
        path = os.path.join(settings.index_path, "index.faiss")
        if not os.path.exists(path):
            return False
        import faiss

        self._index = faiss.read_index(path)
        with open(os.path.join(settings.index_path, "meta.pkl"), "rb") as f:
            self._metas = pickle.load(f)
        return True


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    words = text.split(" ")
    chunks: list[str] = []
    for i in range(0, len(words), size - overlap):
        chunks.append(" ".join(words[i : i + size]))
    return chunks
