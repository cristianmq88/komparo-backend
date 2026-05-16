"""
Worker que se ejecuta diariamente en Railway para actualizar precios.

Para configurar en Railway:
1. Settings → "Cron Schedule"
2. Schedule: 0 4 * * *  (todos los días a las 4 AM)
3. Command: python -m scrapers.run_scrapers
"""
import logging
import sys
from datetime import datetime

from scrapers.run_scrapers import run_all

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        stream=sys.stdout
    )
    
    logger = logging.getLogger("cron")
    logger.info(f"⏰ Cron worker iniciado: {datetime.utcnow().isoformat()}")
    
    try:
        # Ejecutar con 30 productos por categoría = ~300 productos por súper
        stats = run_all(products_per_category=30)
        
        logger.info(f"✅ Worker completado correctamente: {stats}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Worker falló: {e}", exc_info=True)
        sys.exit(1)
