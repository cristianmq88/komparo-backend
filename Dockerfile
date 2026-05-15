FROM python:3.12-slim

WORKDIR /app

# Solo dependencias mínimas (sin Playwright/Chromium)
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Migraciones automáticas al arrancar (si fallan, no detiene el deploy)
RUN alembic upgrade head || true

EXPOSE 8000

# Railway asigna el puerto en la variable $PORT
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
