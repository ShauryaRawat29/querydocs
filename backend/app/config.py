from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    index_path: str = "/tmp/querydocs/faiss_index"
    max_context_chunks: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 100

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
