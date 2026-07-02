# ── Etapa 1: compilar la web (React + Vite) ──────────────────────────
FROM node:20-slim AS frontend
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# VITE_API_BASE vacío => la web llama a la API en el mismo origen (/auth, ...)
ENV VITE_API_BASE=""
RUN npm run build


# ── Etapa 2: backend (FastAPI) + web compilada ───────────────────────
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Copiar la web ya compilada para que FastAPI la sirva en /
COPY --from=frontend /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
