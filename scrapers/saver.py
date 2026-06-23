"""
Guarda los productos raspados en la base de datos.
Maneja:
- Deduplicación (mismo producto desde varios súper)
- Histórico de precios
- Logs de ejecución
"""
import logging
import re
from datetime import datetime
from difflib import SequenceMatcher

from sqlalchemy.orm import Session
from sqlalchemy import and_

# Estos imports asumen que añades los modelos al backend.
# Cambia las rutas si tu estructura es distinta.
from db.models_prices import Product, CurrentPrice, PriceHistory, ScraperRun
from scrapers.base_scraper import ScrapedProduct, ScraperResult

logger = logging.getLogger(__name__)


class PriceSaver:
    """Persiste los productos raspados en la base de datos."""
    
    # Umbral de similitud para considerar dos productos como el mismo
    SIMILARITY_THRESHOLD = 0.75
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_result(self, result: ScraperResult) -> dict:
        """
        Guarda todos los productos de un ScraperResult.
        Devuelve estadísticas de la operación.
        """
        run = self._start_run(result)
        stats = {
            "scraped": len(result.products),
            "new_products": 0,
            "updated_prices": 0,
            "errors": 0
        }
        
        for scraped in result.products:
            try:
                # Buscar si ya existe este producto (o uno muy similar)
                product = self._find_or_create_product(scraped)
                if product._is_new:
                    stats["new_products"] += 1
                
                # Actualizar precio actual
                price_changed = self._update_current_price(product, scraped)
                if price_changed:
                    stats["updated_prices"] += 1
                
                # Añadir al histórico
                self._add_to_history(product, scraped)
                
            except Exception as e:
                logger.error(f"Error guardando {scraped.name}: {e}")
                stats["errors"] += 1
        
        self.db.commit()
        # Éxito si se guardó algo y los errores no superan la mitad del lote.
        success = stats["scraped"] > 0 and stats["errors"] <= stats["scraped"] // 2
        self._finish_run(run, stats, success=success)
        
        return stats
    
    def _find_or_create_product(self, scraped: ScrapedProduct) -> Product:
        """
        Busca un producto existente similar o crea uno nuevo.
        Estrategia:
        1. Buscar exactamente por nombre normalizado
        2. Si no, buscar por similitud
        3. Si no hay, crear nuevo
        """
        # 1. Match exacto
        existing = self.db.query(Product).filter(
            Product.normalized_name == scraped.normalized_name
        ).first()
        
        if existing:
            existing._is_new = False
            return existing
        
        # 2. Match por similitud (buscar entre productos de la misma categoría)
        if scraped.category:
            candidates = self.db.query(Product).filter(
                Product.category == scraped.category
            ).all()
            
            best_match = None
            best_score = 0
            
            for cand in candidates:
                score = SequenceMatcher(
                    None,
                    scraped.normalized_name,
                    cand.normalized_name
                ).ratio()
                if score > best_score and score >= self.SIMILARITY_THRESHOLD:
                    best_score = score
                    best_match = cand
            
            if best_match:
                logger.debug(f"  Match: '{scraped.name}' ≈ '{best_match.name}' ({best_score:.2f})")
                best_match._is_new = False
                return best_match
        
        # 3. Crear nuevo
        new_product = Product(
            name=scraped.name,
            normalized_name=scraped.normalized_name,
            category=scraped.category,
            brand=scraped.brand,
            image_url=scraped.image_url,
            unit_type=scraped.unit_type,
            unit_size=scraped.unit_size
        )
        self.db.add(new_product)
        self.db.flush()  # Para obtener el ID antes del commit
        new_product._is_new = True
        return new_product
    
    def _update_current_price(self, product: Product, scraped: ScrapedProduct) -> bool:
        """
        Actualiza el precio actual del producto en ese supermercado.
        Devuelve True si el precio cambió.
        """
        current = self.db.query(CurrentPrice).filter(
            and_(
                CurrentPrice.product_id == product.id,
                CurrentPrice.supermarket == scraped.supermarket
            )
        ).first()
        
        if current:
            # Actualizar
            price_changed = float(current.price) != scraped.price
            current.price = scraped.price
            current.price_per_unit = scraped.price_per_unit
            current.in_stock = scraped.in_stock
            current.last_seen = datetime.utcnow()
            current.external_id = scraped.external_id
            current.product_url = scraped.product_url
            return price_changed
        else:
            # Crear nuevo
            new_price = CurrentPrice(
                product_id=product.id,
                supermarket=scraped.supermarket,
                external_id=scraped.external_id,
                price=scraped.price,
                price_per_unit=scraped.price_per_unit,
                in_stock=scraped.in_stock,
                product_url=scraped.product_url
            )
            self.db.add(new_price)
            return True
    
    def _add_to_history(self, product: Product, scraped: ScrapedProduct):
        """Añade al histórico (solo si no hay un registro de hoy)."""
        from datetime import date
        today_start = datetime.combine(date.today(), datetime.min.time())
        
        existing_today = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.product_id == product.id,
                PriceHistory.supermarket == scraped.supermarket,
                PriceHistory.recorded_at >= today_start
            )
        ).first()
        
        if not existing_today:
            history = PriceHistory(
                product_id=product.id,
                supermarket=scraped.supermarket,
                price=scraped.price
            )
            self.db.add(history)
    
    def _start_run(self, result: ScraperResult) -> ScraperRun:
        """Registra el inicio de una ejecución."""
        run = ScraperRun(
            supermarket=result.supermarket,
            started_at=result.started_at,
            status="running"
        )
        self.db.add(run)
        self.db.commit()
        return run
    
    def _finish_run(self, run: ScraperRun, stats: dict, success: bool):
        """Marca la ejecución como completada."""
        run.finished_at = datetime.utcnow()
        run.products_scraped = stats["scraped"]
        run.products_updated = stats["updated_prices"]
        run.errors = stats["errors"]
        run.status = "success" if success else "failed"
        self.db.commit()
