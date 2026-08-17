FROM python:3.12-slim

WORKDIR /app

# Install Python deps + a CPU-only torch (kept lightweight for CPU inference).
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy only the app package + env, so uvicorn can import `app.main`.
COPY backend/.env.example /app/.env.example
COPY backend/app ./app

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
