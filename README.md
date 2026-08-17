# QueryDocs
> AI/RAG document Q&A — upload a PDF/TXT/MD/DOCX and ask grounded questions.
> FastAPI backend + Next.js 15 frontend. **Works with zero API keys.**

## Features
- **Retrieval-Augmented Generation**: embeds your document, stores it in a persisted FAISS index, and answers with evidence — no hallucinated claims about content that isn't there.
- **Zero-cost mode**: with no LLM key, answers default to the top-matching passages (extractive). Add a free [Groq](https://console.groq.com) or OpenAI key for natural-language synthesis.
- **Stateless & deployable** on Render (free tier) + Vercel.
- **Explainable**: the LLM is prompted to answer *only* from the provided context, so every answer cites the chunks it used.

## Stack
- **Python** · FastAPI · UVICORN · pydantic · sentence-transformers · FAISS · httpx
- **TypeScript** · Next.js 15 (App Router) · React

## Local dev

### Backend
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt   # + torch (CPU)
uvicorn app.main:app --reload
# -> http://localhost:8000   (Swagger UI at /docs)
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# -> http://localhost:3000 (proxies /api to the backend)
```

## API
- `GET /api/health`
- `POST /api/ingest` — `title` (str) + `file` (multipart) → chunks indexed
- `POST /api/query` — `{"question": "..."}` → `{"answer","sources","provider"}`

## Optional env
```
GROQ_API_KEY=...        # enables Llama 3 synthesis via Groq
OPENAI_API_KEY=...      # enables GPT-4o-mini synthesis
```

## Deploy
```yaml
# render.yaml handles the backend; link this repo folder to Render "Web Service".
```

## Notes
- Embeddings use `all-MiniLM-L6-v2` (cached after first run).
- Documents are never sent over the wire to a third party unless you set `GROQ_API_KEY`/`OPENAI_API_KEY`.
