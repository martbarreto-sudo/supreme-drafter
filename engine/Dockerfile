# syntax=docker/dockerfile:1.7

# ============================================================
# Build stage — uv resolve deps + cria venv com lockfile
# ============================================================
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# uv via pip — mais rápido que baixar tarball para um único stage
RUN pip install --no-cache-dir uv==0.5.11

WORKDIR /build

# Copiar só metadata primeiro para cache eficiente de deps
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Sync sem deps de dev (pytest etc não vão para imagem de produção).
# --frozen falha se lockfile estiver fora de sync — garante build reproduzível.
RUN uv sync --frozen --no-dev


# ============================================================
# Runtime stage — imagem mínima rodando como não-root
# ============================================================
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    CASO_DATA_DIR="/data/feitos"

# Usuário não-root + diretório de dados
RUN groupadd -r nexus && useradd -r -g nexus -d /app -s /sbin/nologin nexus \
    && mkdir -p /data/feitos /app \
    && chown -R nexus:nexus /data /app

WORKDIR /app

# Copia venv pronto + source + migrations + alembic.ini
COPY --from=builder --chown=nexus:nexus /build/.venv ./.venv
COPY --chown=nexus:nexus src/ ./src/
COPY --chown=nexus:nexus alembic/ ./alembic/
COPY --chown=nexus:nexus alembic.ini ./

# pythonpath para resolver `nexus` (espelha o pyproject src/ layout)
ENV PYTHONPATH=/app/src

USER nexus

EXPOSE 8000

# Railway injeta $PORT; default 8000 fora dele.
# Migrations rodam ANTES do uvicorn — crashes aqui impedem start
# servindo versão antiga sem schema novo.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn nexus.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
