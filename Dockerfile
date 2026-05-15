FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Railway pasa el puerto en la variable $PORT
# Usamos shell form para que se interprete la variable
CMD exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
