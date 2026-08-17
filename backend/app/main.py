from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    Embedder._get()
    store = VectorStore(Embedder._get())
    if not store.load():
        # Empty on first boot; will be populated by POST /ingest.
        pass
    rag = RAG(store)
    app.state.rag = rag
    yield


app = FastAPI(title="QueryDocs", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "provider": LLM.provider()}


@app.post("/api/ingest")
def ingest(title: str, file: UploadFile = File(...)):  # noqa: B008
    rag: RAG = app.state.rag
    try:
        result = rag.ingest(title, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"doc_id": result.doc_id, "chunks": result.chunks, "title": result.title, "index_path": settings.index_path}


@app.post("/api/query")
def query(req: QueryRequest) -> QueryResponse:
    rag: RAG = app.state.rag
    result = rag.query(req.question)
    return QueryResponse(answer=result.answer, sources=result.sources, provider=result.provider)
