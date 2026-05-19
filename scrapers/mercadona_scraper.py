"""
Scraper de Mercadona.

Mercadona NO tiene API oficial; usamos la API interna de "Mi Mercadona".
Requiere código postal (precios varían por zona).
"""
import logging
import time
from typing import Optional

from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class MercadonaScraper(BaseScraper):
    SUPERMARKET_ID = "mercadona"
    SUPERMARKET_NAME = "Mercadona"
    BASE_URL = "https://tienda.mercadona.es"
    REQUEST_DELAY = 2.5
    WAREHOUSE = "mad1"  # Warehouse Madrid

    # Categorías → IDs internos (pueden cambiar; descúbrelos en DevTools)
    CATEGORIES = {
        "lacteos": [112, 113, 114, 115, 116],
        "panaderia": [157, 158, 159],
        "huevos": [134],
        "carnes": [200, 201, 202, 203],
        "pescados": [212, 213, 214],
        "aceites": [177, 178],
        "pasta": [142, 143, 144],
        "frutas": [109, 110],
        "verduras": [108],
        "bebidas": [183, 184, 185],
    }

    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        if category not in self.CATEGORIES:
            return []

        category_ids = self.CATEGORIES[category]
        per_cat = max(1, limit // len(category_ids))
        all_products: list[ScrapedProduct] = []

        for cat_id in category_ids:
            try:
                products = self._fetch_category(cat_id, limit=per_cat)
                all_products.extend(products)
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"  Error en categoría {cat_id}: {e}")

        return all_products[:limit]

    def _fetch_category(self, category_id: int, limit: int) -> list[ScrapedProduct]:
        url = f"{self.BASE_URL}/api/categories/{category_id}/"
        data = self.fetch_json(url, params={"wh": self.WAREHOUSE})
        if not data:
            return []

        items: list[dict] = []
        if "categories" in data:
            for subcat in data["categories"]:
                items.extend(subcat.get("products", []))
        elif "products" in data:
            items = data["products"]

        products = []
        for item in items[:limit]:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error parseando: {e}")
        return products

    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        name = item.get("display_name") or item.get("name")
        if not name:
            return None

        price_info = item.get("price_instructions", {}) or {}
        price = self.parse_price(price_info.get("unit_price"))
        if not price:
            return None

        external_id = str(item.get("id", ""))
        if not external_id:
            return None

        price_per_unit = self.parse_price(price_info.get("reference_price"))

        ref_format = (price_info.get("reference_format") or "").lower()
        unit_type = None
        if "kg" in ref_format:
            unit_type = "kg"
        elif "l" in ref_format:
            unit_type = "l"

        size_text = item.get("size_format") or item.get("packaging") or ""
        unit_size, parsed_unit = self.parse_unit(size_text or name)
        if not unit_type and parsed_unit:
            unit_type = parsed_unit

        share_url = item.get("share_url", "")
        if share_url and not share_url.startswith("http"):
            product_url = self.BASE_URL + share_url
        else:
            product_url = share_url or None

        return ScrapedProduct(
            name=name,
            price=price,
            external_id=external_id,
            supermarket=self.SUPERMARKET_ID,
            brand=item.get("brand") or self._guess_brand(name),
            image_url=item.get("thumbnail"),
            product_url=product_url,
            unit_size=unit_size,
            unit_type=unit_type,
            price_per_unit=price_per_unit,
            in_stock=not item.get("unavailable_from"),
        )

    @staticmethod
    def _guess_brand(name: str) -> Optional[str]:
        lower = name.lower()
        if "hacendado" in lower:
            return "Hacendado"
        if "deliplus" in lower:
            return "Deliplus"
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = MercadonaScraper()
    result = scraper.run(categories=["lacteos"], products_per_category=10)
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}  ({p.brand or 'sin marca'})")
