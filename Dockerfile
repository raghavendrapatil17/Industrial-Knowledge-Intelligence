# Industrial Knowledge Intelligence — container image
FROM python:3.12-slim

WORKDIR /app

# system libs needed by the OCR engine (opencv) for image ingestion
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# build the corpus + index + knowledge graph at image-build time so the container is demo-ready
RUN python scripts/generate_corpus.py && python scripts/build_index.py

ENV LLM_PROVIDER=offline
EXPOSE 8000

# honour the platform's $PORT (Render / HF Spaces / Railway); default 8000. 0.0.0.0 = reachable externally.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
