from __future__ import annotations

from backend.app.vectorstore import chunk_text


def test_chunk_text_splits_long_text():
    text = "word " * 100
    chunks = chunk_text(text, size=20, overlap=5)
    assert len(chunks) >= 2
    assert all(len(c.split()) <= 20 for c in chunks)


def test_chunk_text_handles_empty():
    assert chunk_text("", size=10, overlap=2) == []
