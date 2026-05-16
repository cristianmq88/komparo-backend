"""
Orquestador principal de scrapers.
Ejecuta todos los scrapers configurados y guarda resultados en BD.

Uso:
    python -m scrapers.run_scrapers          # Todos
    python -m scrapers.run_scrapers carrefour # Solo Carrefour
"""
import logging
import sys
from datetime import datetime

from sqlalchemy.orm import sessionmaker
from db.database import engine  # Tu engine SQLAlchemy

from scrapers.carrefour_scraper import CarrefourScraper
from scrapers.mercadona_scraper import MercadonaScraper
from scrapers.dia_scraper import DiaScraper
from scrapers.alcampo_scraper import AlcampoScraper
from scrapers.saver import PriceSaver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# Registro de scrapers disponibles
SCRAPERS = {
    "carrefour": CarrefourScraper,
    "mercadona": MercadonaScraper,
    "dia": DiaScraper,
    "alcampo": AlcampoScraper
}


def run_scraper(scraper_id: str, products_per_category: int = 30):
    """Ejecuta un scraper individual."""
    if scraper_id not in SCRAPERS:
        logger.error(f"Scraper desconocido: {scraper_id}")
        return None
    
    ScraperClass = SCRAPERS[scraper_id]
    scraper = ScraperClass()
    
    # Ejecutar
    try:
        result = scraper.run(products_per_category=products_per_category)
    except Exception as e:
        logger.error(f"❌ {scraper_id} crasheó: {e}", exc_info=True)
        return None
    
    # Guardar en BD
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        saver = PriceSaver(db)
        stats = saver.save_result(result)
        logger.info(f"💾 {scraper_id} guardado: {stats}")
        return stats
    finally:
        db.close()


def run_all(products_per_category: int = 30):
    """Ejecuta todos los scrapers en secuencia."""
    logger.info("=" * 70)
    logger.info(f"🚀 INICIANDO TODOS LOS SCRAPERS  -  {datetime.utcnow().isoformat()}")
    logger.info("=" * 70)
    
    total_stats = {
        "scrapers_run": 0,
        "scrapers_success": 0,
        "total_products": 0,
        "total_updates": 0
    }
    
    for scraper_id in SCRAPERS:
        logger.info(f"\n{'─' * 70}")
        logger.info(f"▶️  {scraper_id.upper()}")
        logger.info(f"{'─' * 70}")
        
        stats = run_scraper(scraper_id, products_per_category)
        total_stats["scrapers_run"] += 1
        
        if stats:
            total_stats["scrapers_success"] += 1
            total_stats["total_products"] += stats["scraped"]
            total_stats["total_updates"] += stats["updated_prices"]
    
    logger.info("\n" + "=" * 70)
    logger.info(f"📊 RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"  Scrapers ejecutados: {total_stats['scrapers_run']}")
    logger.info(f"  Con éxito:           {total_stats['scrapers_success']}")
    logger.info(f"  Productos raspados:  {total_stats['total_products']}")
    logger.info(f"  Precios actualizados:{total_stats['total_updates']}")
    
    return total_stats


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scraper_id = sys.argv[1].lower()
        run_scraper(scraper_id)
    else:
        run_all()
