from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import UploadFile


@dataclass
class IngestResult:
    doc_id: str
    chunks: int
    title: str


@dataclass
class QueryResult:
    answer: str
    sources: list[str] = field(default_factory=list)
    provider: str | None = None


def allowed_file(file: UploadFile) -> bool:
    ct = (file.content_type or "").lower()
    return ct in {
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
    }
