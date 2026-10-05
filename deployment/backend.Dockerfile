FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY ai_engine ./ai_engine
COPY crawler ./crawler
COPY database ./database
COPY indexer ./indexer
COPY knowledge_graph ./knowledge_graph
COPY model_cache.py .
COPY reranker ./reranker
COPY retrieval ./retrieval
COPY search_engine ./search_engine
COPY scripts ./scripts
COPY config ./config

RUN useradd --create-home --uid 10001 nexus \
    && mkdir -p /app/database /app/private_vault/documents /app/.cache \
    && chown -R nexus:nexus /app

USER nexus
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
