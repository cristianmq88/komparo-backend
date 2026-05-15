FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para Playwright y psycopg2
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegador Chromium para Playwright (Ahorramas/Dia)
RUN playwright install chromium --with-deps

COPY . .

# Migraciones automáticas al arrancar
RUN alembic upgrade head || true

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
