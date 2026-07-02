# Industrial Knowledge Intelligence — container image
FROM python:3.12-slim

WORKDIR /app

# system deps kept minimal (pure-python stack)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# build the index + knowledge graph at image-build time so the container is demo-ready
RUN python scripts/generate_corpus.py && python scripts/build_index.py

EXPOSE 8000
ENV LLM_PROVIDER=offline

# 0.0.0.0 so the port is reachable from outside the container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
