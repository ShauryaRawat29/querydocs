# Deploying QueryDocs

The project is split into a **backend** (FastAPI, Render) and a **frontend**
(Next.js, Vercel). Both are free-tier friendly.

> You must create the services using **your own** Render and Vercel accounts —
> the repo just provides the config (`render.yaml`, `Dockerfile`, `frontend/`).

## 1) Backend (FastAPI) → Render

Render auto-builds the Docker image from `render.yaml`.

1. Go to https://render.com and sign in (GitHub auth is fine).
2. Click **New → Web Service** (or open an existing one) and select
   `ShauryaRawat29/querydocs`.
3. Render auto-detects `render.yaml` (a "Blueprint"). Review:
   - **Name:** `querydocs-api`
   - **Region:** `Oregon` (closest to most of Asia/Europe/US free tier)
   - **Plan:** **Free** (sufficient for a demo/resume project)
4. Environment variables (click the service → Environment):
   - `GROQ_API_KEY` — optional. If set, answers are synthesized by Llama 3.
     **Leave unset** → zero-cost extractive answers (top-matching chunks).
   - `OPENAI_API_KEY` — optional alternative.
   - (Everything else comes from `render.yaml`.)
5. Click **Update Deploys** / create. Build takes ~2–4 min (it installs
   CPU-only torch + sentence-transformers). The health check
   `GET /api/health` returns `{"ok": true, ...}`.

> The FAISS index lives in `/tmp/querydocs/` inside the container, which
> persists while the service runs. Re-ingest after a restart.

## 2) Frontend (Next.js) → Vercel

1. Go to https://vercel.com → **New Project** → import `ShauryaRawat29/querydocs`.
2. In **Configure Project**:
   - **Root Directory:** `frontend`
   - (Framework preset auto-detects Next.js.)
3. Environment Variables → Add:
   - `NEXT_PUBLIC_API_URL` = the Render backend URL, e.g.
     `https://querydocs-api.onrender.com`
   - (Optional) `NEXT_PUBLIC_API_URL` for local dev = `http://localhost:8000`.
4. Click **Deploy**. The `/api/*` calls proxy through `next.config.mjs` so
   there are no CORS issues.

## 3) Smoke test (after both are live)

```
curl -X POST https://<your-render-url>/api/ingest -F "title=notes" -F "file=@sample.txt"
curl -X POST https://<your-render-url>/api/query -H "Content-Type: application/json" \
  -d '{"question":"What is quantum computing?"}'
```

For a zero-cost demo, skip both LLM keys — answers come back as the top
matching chunk(s).
