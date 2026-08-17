from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .embeddings import Embedder
from .llm import LLM
from .rag import RAG
from .vectorstore import VectorStore


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    provider: str | None = None


app = FastAPI(title="QueryDocs", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_rag() -> RAG:
    """Lazily build (and cache) the RAG pipeline on first request.

    Using a dependency instead of startup logic keeps cold-start latency low on
    serverless/Render free-tier containers and avoids failing to boot when the
    embedding model is slow to load.
    """
    cached = getattr(app.state, "rag", None)
    if cached is None:
        Embedder._get()
        store = VectorStore(Embedder._get())
        store.load()
        cached = RAG(store)
        app.state.rag = cached
    return cached


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "provider": LLM.provider()}


@app.post("/api/ingest")
def ingest(title: str = Form(...), file: UploadFile = File(...)):  # noqa: B008
    rag = get_rag()
    try:
        result = rag.ingest(title, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "doc_id": result.doc_id,
        "chunks": result.chunks,
        "title": result.title,
        "index_path": settings.index_path,
    }


@app.post("/api/query")
def query(req: QueryRequest) -> QueryResponse:
    rag: RAG = get_rag()
    result = rag.query(req.question)
    return QueryResponse(
        answer=result.answer, sources=result.sources, provider=result.provider
    )
