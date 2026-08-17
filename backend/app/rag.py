from __future__ import annotations

import io

from fastapi import UploadFile

from .config import settings
from .embeddings import Embedder
from .llm import LLM
from .schemas import IngestResult, QueryResult
from .vectorstore import DocChunk, VectorStore, chunk_text


def extract_text(file: UploadFile) -> str:
    raw = file.file.read()
    if file.filename and file.filename.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw.decode("utf-8", errors="replace")


class RAG:
    """Retrieval-Augmented Generation pipeline.

    Embeds docs with sentence-transformers, stores them in a persisted FAISS
    index, then optionally synthesizes an answer with an LLM (Groq/OpenAI).
    Without any LLM key it still works via an extractive fallback.
    """

    def __init__(self, store: VectorStore) -> None:
        self.store = store
        self.embedder = Embedder

    def ingest(self, title: str, file: UploadFile) -> IngestResult:
        text = extract_text(file)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("Uploaded document produced no readable text.")
        embs = self.embedder.embed_chunks(chunks)
        docs = [DocChunk(doc_id=title, chunk_index=i, text=c) for i, c in enumerate(chunks)]
        self.store.add(docs, embs)
        self.store.persist()
        return IngestResult(doc_id=title, chunks=len(chunks), title=title)

    def query(self, question: str) -> QueryResult:
        qvec = self.embedder.embed_text(question)
        hits = self.store.search(qvec, k=settings.max_context_chunks)
        if not hits:
            return QueryResult(
                answer="No documents ingested yet. Upload a file first.",
                provider=LLM.provider(),
            )
        context = "\n---\n".join(h.text for h in hits)
        answer = LLM.answer(question, context)
        return QueryResult(
            answer=answer,
            sources=[h.text[:200] + "..." for h in hits],
            provider=LLM.provider(),
        )
