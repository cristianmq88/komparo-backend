"""
Orquestador de scrapers.

Uso:
    python -m scrapers.run_scrapers           # Todos
    python -m scrapers.run_scrapers carrefour # Solo Carrefour
"""
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

from db.database import SessionLocal
from scrapers.alcampo_scraper import AlcampoScraper
from scrapers.base_scraper import BaseScraper
from scrapers.carrefour_scraper import CarrefourScraper
from scrapers.dia_scraper import DiaScraper
from scrapers.mercadona_scraper import MercadonaScraper
from scrapers.saver import PriceSaver

logger = logging.getLogger(__name__)


SCRAPERS: dict[str, type[BaseScraper]] = {
    "carrefour": CarrefourScraper,
    "mercadona": MercadonaScraper,
    "dia": DiaScraper,
    "alcampo": AlcampoScraper,
}


def run_scraper(scraper_id: str, products_per_category: int = 30) -> Optional[dict]:
    """Ejecuta un scraper individual y persiste resultados."""
    scraper_cls = SCRAPERS.get(scraper_id)
    if not scraper_cls:
        logger.error(f"Scraper desconocido: {scraper_id}")
        return None

    try:
        result = scraper_cls().run(products_per_category=products_per_category)
    except Exception as e:
        logger.error(f"❌ {scraper_id} crasheó: {e}", exc_info=True)
        return None

    db = SessionLocal()
    try:
        stats = PriceSaver(db).save_result(result)
        logger.info(f"💾 {scraper_id} guardado: {stats}")
        return stats
    finally:
        db.close()


def run_all(products_per_category: int = 30) -> dict:
    """Ejecuta todos los scrapers en secuencia."""
    logger.info("=" * 70)
    logger.info(f"🚀 INICIANDO TODOS LOS SCRAPERS  -  {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 70)

    totals = {
        "scrapers_run": 0,
        "scrapers_success": 0,
        "total_products": 0,
        "total_updates": 0,
    }

    for scraper_id in SCRAPERS:
        logger.info(f"\n{'─' * 70}\n▶️  {scraper_id.upper()}\n{'─' * 70}")
        stats = run_scraper(scraper_id, products_per_category)
        totals["scrapers_run"] += 1
        if stats:
            totals["scrapers_success"] += 1
            totals["total_products"] += stats["scraped"]
            totals["total_updates"] += stats["updated_prices"]

    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"  Scrapers ejecutados:   {totals['scrapers_run']}")
    logger.info(f"  Con éxito:             {totals['scrapers_success']}")
    logger.info(f"  Productos raspados:    {totals['total_products']}")
    logger.info(f"  Precios actualizados:  {totals['total_updates']}")
    return totals


def main(argv: list[str]) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    try:
        if len(argv) > 1:
            return 0 if run_scraper(argv[1].lower()) else 1
        run_all()
        return 0
    except Exception as e:
        logger.error(f"❌ Worker falló: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
