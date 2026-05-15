"""
scheduler/tasks.py — Tareas programadas de scraping con Celery

El scraping se ejecuta de madrugada (2:00 - 5:00 AM) para:
  - Minimizar impacto en los servidores de los supermercados
  - Tener precios frescos disponibles para el horario de compra (mañana)
  - Repartir la carga entre supermercados para no saturar la IP
"""
import asyncio
import logging
from datetime import datetime
from celery import group
from .celery_app import celery_app
from scrapers.mercadona   import MercadonaScraper
from scrapers.carrefour   import CarrefourScraper
from scrapers.alcampo     import AlcampoScraper
from scrapers.all_scrapers import (
    DiaScraper, LidlScraper, AhorramasScraper, AldiScraper, CorteInglesScraper
)
from db.crud import upsert_products, update_last_scraped

logger = logging.getLogger(__name__)

SCRAPERS = {
    "mercadona":   MercadonaScraper,
    "carrefour":   CarrefourScraper,
    "alcampo":     AlcampoScraper,
    "dia":         DiaScraper,
    "lidl":        LidlScraper,
    "ahorramas":   AhorramasScraper,
    "aldi":        AldiScraper,
    "corteingles": CorteInglesScraper,
}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def scrape_supermarket(self, supermarket_id: str):
    """
    Tarea por supermercado — se puede lanzar individualmente o en grupo.
    """
    logger.info(f"Iniciando scraping: {supermarket_id}")
    try:
        scraper_cls = SCRAPERS[supermarket_id]
        scraper     = scraper_cls()
        # Ejecutar el scraper async dentro del contexto sync de Celery
        products = asyncio.run(scraper.scrape_all())
        # Guardar en la BD
        saved = upsert_products(supermarket_id, products)
        update_last_scraped(supermarket_id)
        logger.info(f"[{supermarket_id}] {saved} productos guardados")
        return {"supermarket": supermarket_id, "products": saved, "status": "ok"}
    except Exception as exc:
        logger.error(f"Error scraping {supermarket_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def scrape_all_supermarkets():
    """
    Lanza el scraping de los 8 supermercados en paralelo (grupo Celery).
    Programado cada noche a las 2:00 AM.
    """
    logger.info("Iniciando scraping nocturno de todos los supermercados")
    job = group(
        scrape_supermarket.s("mercadona"),    # 02:00 — API limpia, rápido
        scrape_supermarket.s("carrefour"),    # 02:10
        scrape_supermarket.s("alcampo"),      # 02:20
        scrape_supermarket.s("corteingles"),  # 02:30 — API disponible
        scrape_supermarket.s("dia"),          # 02:45 — necesita cookies
        scrape_supermarket.s("lidl"),         # 03:00
        scrape_supermarket.s("aldi"),         # 03:15
        scrape_supermarket.s("ahorramas"),    # 03:30 — Playwright, más lento
    )
    result = job.apply_async()
    return result.id


# ── Programación (beat schedule) ─────────────────────────────────────────────
# Se configura en celery_app.py con beat_schedule
