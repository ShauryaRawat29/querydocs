from __future__ import annotations

import os
import pickle
import re
import io
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sentence_transformers import SentenceTransformer
import httpx

from .config import settings

if TYPE_CHECKING:
    from .vectorstore import VectorStore


@dataclass
class DocChunk:
    doc_id: str
    chunk_index: int
    text: str
    meta: dict | None = None


_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embed_model)
    return _model


def embed_text(text: str) -> list[float]:
    return get_model().encode([text], normalize_embeddings=True).tolist()[0]


def embed_chunks(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, normalize_embeddings=True).tolist()


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    words = text.split(" ")
    chunks: list[str] = []
    for i in range(0, len(words), size - overlap):
        chunks.append(" ".join(words[i : i + size]))
    return chunks


class VectorStore:
    """Persistable FAISS index keyed by doc_id."""

    def __init__(self) -> None:
        self._index = None
        self._metas: list[DocChunk] = []
        self._model = get_model()

    def _import_faiss(self):
        import faiss
        return faiss

    def _ensure_index(self, dim: int) -> None:
        if self._index is not None:
            return
        faiss = self._import_faiss()
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
        self._import_faiss()
        k = min(k, len(self._metas))
        _dist, idxs = self._index.search(np.array([query_vec], dtype="float32"), k)
        return [self._metas[i] for i in idxs[0] if i != -1]

    def persist(self) -> None:
        if self._index is None:
            return
        os.makedirs(settings.index_path, exist_ok=True)
        faiss = self._import_faiss()
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


def extract_text(file) -> str:
    raw = file.file.read()
    if file.filename and file.filename.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw.decode("utf-8", errors="replace")


def llm_provider() -> str | None:
    if settings.groq_api_key:
        return "groq"
    if settings.openai_api_key:
        return "openai"
    return None


def llm_answer(query: str, context: str) -> str:
    provider = llm_provider()
    if provider == "groq":
        return _groq(query, context)
    if provider == "openai":
        return _openai(query, context)
    return context[:1200] or "Could not find an answer in the provided documents."


def _groq(query: str, context: str) -> str:
    sys = "You are a helpful assistant that answers ONLY from the provided context."
    prompt = f"Context:\n{context}\n\nQuestion: {query}"
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "system", "content": sys}, {"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 512,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _openai(query: str, context: str) -> str:
    sys = "You are a helpful assistant that answers ONLY from the provided context."
    prompt = f"Context:\n{context}\n\nQuestion: {query}"
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": sys}, {"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 512,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


@dataclass
class IngestResult:
    doc_id: str
    chunks: int
    title: str


@dataclass
class QueryResult:
    answer: str
    sources: list[str]
    provider: str | None


class RAG:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(self, store: VectorStore) -> None:
        self.store = store

    def ingest(self, title: str, file) -> IngestResult:
        text = extract_text(file)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("Uploaded document produced no readable text.")
        embs = embed_chunks(chunks)
        docs = [DocChunk(doc_id=title, chunk_index=i, text=c) for i, c in enumerate(chunks)]
        self.store.add(docs, embs)
        self.store.persist()
        return IngestResult(doc_id=title, chunks=len(chunks), title=title)

    def query(self, question: str) -> QueryResult:
        qvec = embed_text(question)
        hits = self.store.search(qvec, k=settings.max_context_chunks)
        if not hits:
            return QueryResult(
                answer="No documents ingested yet. Upload a file first.",
                sources=[],
                provider=llm_provider(),
            )
        context = "\n---\n".join(h.text for h in hits)
        answer = llm_answer(question, context)
        return QueryResult(
            answer=answer,
            sources=[h.text[:200] + "..." for h in hits],
            provider=llm_provider(),
        )