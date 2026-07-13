# Imagem unica do pipeline NEXUM TIER 0.
#
# Um mesmo artefato roda:
#   - o consumidor (default CMD): uvicorn nexum.consumer.asgi:app
#   - o relay (override de comando): python -m nexum.relay.worker
#
# Contexto de build esperado: RAIZ do repositorio (o compose usa context: .).
FROM python:3.12-slim

WORKDIR /app

# Dependencias primeiro para aproveitar o cache de camadas.
COPY nexum/requirements.txt ./nexum/requirements.txt
RUN pip install --no-cache-dir -r nexum/requirements.txt

# Codigo da aplicacao.
COPY nexum/ ./nexum/

EXPOSE 8000

# Default: consumidor idempotente (FastAPI via uvicorn). O app de nivel de
# modulo em nexum.consumer.asgi le REDIS_URL do ambiente.
CMD ["uvicorn", "nexum.consumer.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
