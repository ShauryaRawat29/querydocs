from __future__ import annotations

import httpx

from .config import settings


class LLM:
    """Optional LLM for answer synthesis.

    Falls back to an extractive answer (top document chunks) when no API key is
    configured, so the app works end-to-end with **zero** paid APIs.
    """

    @staticmethod
    def provider() -> str | None:
        if settings.groq_api_key:
            return "groq"
        if settings.openai_api_key:
            return "openai"
        return None

    @classmethod
    def answer(cls, query: str, context: str) -> str:
        if cls.provider() == "groq":
            return cls._groq(query, context)
        if cls.provider() == "openai":
            return cls._openai(query, context)
        # Extractive fallback: just surface a slice of the retrieved context.
        return context[:1200] or "Could not find an answer in the provided documents."

    @classmethod
    def _groq(cls, query: str, context: str) -> str:
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

    @classmethod
    def _openai(cls, query: str, context: str) -> str:
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
