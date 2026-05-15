"""
api/main.py — FastAPI: punto de entrada de la API REST de Komparo

Versión simplificada para arranque inicial.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# CREAR APP
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Komparo API",
    description="API de comparador de precios de supermercados Madrid",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS BÁSICOS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    """Endpoint raíz - estado de la API"""
    return {
        "app": "Komparo API",
        "version": "1.0.0",
        "status": "running",
        "message": "Listas que comparan, decisiones que ahorran"
    }


@app.get("/health")
def health_check():
    """Health check para Railway"""
    return {"status": "healthy"}


@app.get("/supermarkets")
def list_supermarkets():
    """Lista de los 8 supermercados de Madrid"""
    return {
        "supermarkets": [
            {"id": "mercadona", "name": "Mercadona", "color": "#0E8C5A"},
            {"id": "carrefour", "name": "Carrefour", "color": "#004E9A"},
            {"id": "alcampo", "name": "Alcampo", "color": "#1E4296"},
            {"id": "dia", "name": "Dia", "color": "#E30613"},
            {"id": "lidl", "name": "Lidl", "color": "#0050AA"},
            {"id": "aldi", "name": "Aldi", "color": "#00529B"},
            {"id": "ahorramas", "name": "Ahorramas", "color": "#FF6B00"},
            {"id": "corteingles", "name": "El Corte Inglés", "color": "#006E42"},
        ]
    }


@app.get("/products/search")
def search_products(q: str = ""):
    """Búsqueda de productos (demo)"""
    if not q:
        return {"products": [], "message": "Proporciona un parámetro 'q' para buscar"}
    
    # Datos de demostración
    return {
        "query": q,
        "products": [
            {
                "id": "demo_1",
                "name": f"{q.title()} (demo)",
                "prices": {
                    "mercadona": 0.84,
                    "alcampo": 0.88,
                    "lidl": 0.86,
                    "carrefour": 0.92,
                    "dia": 0.89,
                    "aldi": 0.85,
                    "ahorramas": 0.91,
                    "corteingles": 1.05,
                }
            }
        ],
        "note": "Versión inicial. Los precios reales se obtendrán cuando los scrapers estén configurados."
    }


# ──────────────────────────────────────────────────────────────────────────────
# STARTUP/SHUTDOWN
# ──────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Komparo API iniciada correctamente")
    db_url = os.getenv("DATABASE_URL", "no configurada")
    if db_url != "no configurada":
        logger.info(f"✅ DATABASE_URL configurada")
    else:
        logger.warning("⚠️  DATABASE_URL no configurada - funcionando en modo demo")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Komparo API detenida")
