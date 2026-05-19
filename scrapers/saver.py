"""
Guarda los productos raspados en la base de datos.
Maneja deduplicación, histórico y logs de ejecución.
"""
import logging
from datetime import date, datetime, timezone
from difflib import SequenceMatcher

from sqlalchemy import and_
from sqlalchemy.orm import Session

from db.models_prices import CurrentPrice, PriceHistory, Product, ScraperRun
from scrapers.base_scraper import ScrapedProduct, ScraperResult

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PriceSaver:
    """Persiste los productos raspados en la base de datos."""

    SIMILARITY_THRESHOLD = 0.75

    def __init__(self, db: Session):
        self.db = db

    def save_result(self, result: ScraperResult) -> dict:
        run = self._start_run(result)
        stats = {
            "scraped": len(result.products),
            "new_products": 0,
            "updated_prices": 0,
            "errors": 0,
        }

        for scraped in result.products:
            try:
                product, is_new = self._find_or_create_product(scraped)
                if is_new:
                    stats["new_products"] += 1

                if self._update_current_price(product, scraped):
                    stats["updated_prices"] += 1

                self._add_to_history(product, scraped)
            except Exception as e:
                logger.error(f"Error guardando {scraped.name}: {e}")
                stats["errors"] += 1

        self.db.commit()
        self._finish_run(run, stats)
        return stats

    def _find_or_create_product(
        self, scraped: ScrapedProduct
    ) -> tuple[Product, bool]:
        """Devuelve (producto, es_nuevo). Estrategia:
        1) Match exacto por nombre normalizado.
        2) Match por similitud dentro de la misma categoría.
        3) Crear nuevo.
        """
        existing = (
            self.db.query(Product)
            .filter(Product.normalized_name == scraped.normalized_name)
            .first()
        )
        if existing:
            return existing, False

        if scraped.category:
            candidates = (
                self.db.query(Product)
                .filter(Product.category == scraped.category)
                .all()
            )
            best_match, best_score = None, 0.0
            for cand in candidates:
                score = SequenceMatcher(
                    None, scraped.normalized_name, cand.normalized_name
                ).ratio()
                if score > best_score and score >= self.SIMILARITY_THRESHOLD:
                    best_score = score
                    best_match = cand
            if best_match:
                logger.debug(
                    f"  Match: '{scraped.name}' ≈ '{best_match.name}' ({best_score:.2f})"
                )
                return best_match, False

        new_product = Product(
            name=scraped.name,
            normalized_name=scraped.normalized_name,
            category=scraped.category,
            brand=scraped.brand,
            image_url=scraped.image_url,
            unit_type=scraped.unit_type,
            unit_size=scraped.unit_size,
        )
        self.db.add(new_product)
        self.db.flush()
        return new_product, True

    def _update_current_price(
        self, product: Product, scraped: ScrapedProduct
    ) -> bool:
        """Actualiza el precio actual. Devuelve True si cambió."""
        current = (
            self.db.query(CurrentPrice)
            .filter(
                and_(
                    CurrentPrice.product_id == product.id,
                    CurrentPrice.supermarket == scraped.supermarket,
                )
            )
            .first()
        )

        if current:
            price_changed = float(current.price) != scraped.price
            current.price = scraped.price
            current.price_per_unit = scraped.price_per_unit
            current.in_stock = scraped.in_stock
            current.last_seen = _utcnow()
            current.external_id = scraped.external_id
            current.product_url = scraped.product_url
            return price_changed

        self.db.add(CurrentPrice(
            product_id=product.id,
            supermarket=scraped.supermarket,
            external_id=scraped.external_id,
            price=scraped.price,
            price_per_unit=scraped.price_per_unit,
            in_stock=scraped.in_stock,
            product_url=scraped.product_url,
        ))
        return True

    def _add_to_history(self, product: Product, scraped: ScrapedProduct) -> None:
        """Añade al histórico, una entrada por día y supermercado."""
        today_start = datetime.combine(date.today(), datetime.min.time())
        already = (
            self.db.query(PriceHistory.id)
            .filter(
                and_(
                    PriceHistory.product_id == product.id,
                    PriceHistory.supermarket == scraped.supermarket,
                    PriceHistory.recorded_at >= today_start,
                )
            )
            .first()
        )
        if already:
            return

        self.db.add(PriceHistory(
            product_id=product.id,
            supermarket=scraped.supermarket,
            price=scraped.price,
        ))

    def _start_run(self, result: ScraperResult) -> ScraperRun:
        run = ScraperRun(
            supermarket=result.supermarket,
            started_at=result.started_at,
            status="running",
        )
        self.db.add(run)
        self.db.commit()
        return run

    def _finish_run(self, run: ScraperRun, stats: dict) -> None:
        scraped = stats["scraped"]
        errors = stats["errors"]
        # Éxito si hubo productos y la tasa de error es < 50 %
        success = scraped > 0 and errors * 2 < scraped

        run.finished_at = _utcnow()
        run.products_scraped = scraped
        run.products_updated = stats["updated_prices"]
        run.errors = errors
        run.status = "success" if success else "failed"
        self.db.commit()
