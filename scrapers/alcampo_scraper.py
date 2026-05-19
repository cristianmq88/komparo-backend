"""
Scraper de Alcampo.

Endpoint: https://www.compraonline.alcampo.es/api/v5/products
"""
import logging
from typing import Optional

from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class AlcampoScraper(BaseScraper):
    SUPERMARKET_ID = "alcampo"
    SUPERMARKET_NAME = "Alcampo"
    BASE_URL = "https://www.compraonline.alcampo.es"
    REQUEST_DELAY = 2.0

    SEARCH_URL = "https://www.compraonline.alcampo.es/api/v5/products"

    CATEGORIES = {
        "lacteos": ["leche", "yogur", "queso"],
        "panaderia": ["pan", "pan molde"],
        "huevos": ["huevos"],
        "carnes": ["pollo", "carne picada"],
        "pescados": ["salmon", "merluza"],
        "aceites": ["aceite oliva"],
        "pasta": ["pasta", "arroz"],
        "frutas": ["platano", "manzana"],
        "verduras": ["patata"],
        "bebidas": ["agua mineral"],
    }

    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        return self._scrape_by_terms(category, limit, self._search)

    def _search(self, query: str, limit: int) -> list[ScrapedProduct]:
        params = {"search_term": query, "limit": limit, "offset": 0}
        data = self.fetch_json(self.SEARCH_URL, params=params)
        if not data:
            return []

        items = (
            data.get("entities", {}).get("product", {})
            or data.get("items", [])
            or data.get("products", [])
        )
        if isinstance(items, dict):
            items = list(items.values())

        products = []
        for item in items:
            try:
                product = self._parse_item(item, query)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error: {e}")
        return products

    def _parse_item(self, item: dict, search_query: str) -> Optional[ScrapedProduct]:
        name = item.get("name") or item.get("title") or item.get("displayName")
        if not name:
            return None

        price_obj = item.get("price", {}) or {}
        price = None
        if isinstance(price_obj, dict):
            current = price_obj.get("current")
            if isinstance(current, dict):
                price = self.parse_price(current.get("amount"))
            elif current is not None:
                price = self.parse_price(current)
            if not price:
                price = self.parse_price(price_obj.get("amount"))
        if not price:
            return None

        external_id = str(
            item.get("retailerProductId") or item.get("id") or item.get("sku", "")
        )
        if not external_id:
            return None

        unit_price = item.get("pricePerUnit") or (
            price_obj.get("unitPrice") if isinstance(price_obj, dict) else None
        )
        if isinstance(unit_price, dict):
            price_per_unit = self.parse_price(unit_price.get("amount"))
        else:
            price_per_unit = self.parse_price(unit_price)

        image = item.get("image")
        if isinstance(image, dict):
            image = image.get("src") or image.get("url")

        size_text = item.get("size") or item.get("packaging") or ""
        unit_size, unit_type = self.parse_unit(size_text or name)

        return ScrapedProduct(
            name=name,
            price=price,
            external_id=external_id,
            supermarket=self.SUPERMARKET_ID,
            brand=item.get("brand"),
            category=search_query,
            image_url=image,
            unit_size=unit_size,
            unit_type=unit_type,
            price_per_unit=price_per_unit,
            in_stock=item.get("available", True),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = AlcampoScraper()
    result = scraper.run(categories=["lacteos"], products_per_category=5)
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}")
