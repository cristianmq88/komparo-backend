# 🛒 SuperApp Backend — Comparador de Precios Madrid

Backend completo para comparar precios en tiempo real de los 8 supermercados
con más presencia en Madrid.

## Supermercados cubiertos
| # | Cadena | Marca blanca | API/Scraping |
|---|--------|-------------|--------------|
| 1 | Mercadona | Hacendado | API interna (JSON limpio) |
| 2 | Carrefour | Carrefour | API interna |
| 3 | Dia | Dia | Scraping web |
| 4 | Lidl | Milbona | Scraping web |
| 5 | Alcampo | Auchan / Prod. Alcampo | API interna |
| 6 | Ahorramas | Bosque Verde | Scraping web |
| 7 | Aldi | Specially Selected | Scraping web |
| 8 | El Corte Inglés (Supercor) | El Corte Inglés | API interna |

## Stack
- **FastAPI** — API REST
- **PostgreSQL** — base de datos principal
- **Redis** — caché de precios y cola de tareas
- **Celery** — scraping programado (cada noche 2:00-5:00 AM)
- **SQLAlchemy** — ORM
- **Playwright** — scraping de webs con JS (Lidl, Aldi, Ahorramas, Dia)
- **httpx** — llamadas a APIs internas (Mercadona, Carrefour, Alcampo, ECI)

## Estructura
```
superapp/
├── scrapers/          # Un scraper por supermercado
│   ├── base.py        # Clase base abstracta
│   ├── mercadona.py
│   ├── carrefour.py
│   ├── dia.py
│   ├── lidl.py
│   ├── alcampo.py
│   ├── ahorramas.py
│   ├── aldi.py
│   └── corteingles.py
├── api/
│   ├── main.py        # FastAPI app
│   ├── routes/
│   │   ├── products.py   # búsqueda y precios
│   │   ├── lists.py      # listas de la compra
│   │   ├── auth.py       # login/registro
│   │   └── compare.py    # comparativa de supermercados
│   └── deps.py           # dependencias (auth, db)
├── db/
│   ├── models.py      # modelos SQLAlchemy
│   ├── schemas.py     # schemas Pydantic
│   └── crud.py        # operaciones de base de datos
├── scheduler/
│   ├── celery_app.py  # configuración Celery
│   └── tasks.py       # tareas de scraping programadas
├── tests/
│   └── test_scrapers.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Inicio rápido
```bash
cp .env.example .env          # configurar variables de entorno
docker-compose up -d          # levanta PostgreSQL + Redis
pip install -r requirements.txt
alembic upgrade head          # crea las tablas
python -m uvicorn api.main:app --reload   # inicia la API
celery -A scheduler.celery_app worker -l info  # inicia el scheduler
```

## Variables de entorno clave (.env)
```
DATABASE_URL=postgresql://user:pass@localhost:5432/superapp
REDIS_URL=redis://localhost:6379
SECRET_KEY=tu_clave_secreta_jwt
MADRID_POSTAL_CODE=28001        # código postal Madrid centro para precios
SCRAPING_INTERVAL_HOURS=12
```
