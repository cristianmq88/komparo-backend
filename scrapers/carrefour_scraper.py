"""
Scraper de Carrefour usando su API pública de búsqueda.

Endpoint: https://www.carrefour.es/search-api/query/v1/search
"""
import logging
from typing import Optional

from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class CarrefourScraper(BaseScraper):
    SUPERMARKET_ID = "carrefour"
    SUPERMARKET_NAME = "Carrefour"
    BASE_URL = "https://www.carrefour.es"
    REQUEST_DELAY = 1.5

    SEARCH_URL = "https://www.carrefour.es/search-api/query/v1/search"

    CATEGORIES = {
        "lacteos": ["leche", "yogur", "queso", "mantequilla"],
        "panaderia": ["pan", "pan de molde", "biscotes"],
        "huevos": ["huevos"],
        "carnes": ["pollo", "carne picada", "bacon", "chorizo"],
        "pescados": ["salmon", "merluza", "atun"],
        "aceites": ["aceite oliva", "aceite girasol"],
        "pasta": ["pasta espagueti", "macarrones", "arroz"],
        "frutas": ["platano", "manzana", "naranja", "tomate"],
        "verduras": ["patata", "cebolla", "lechuga", "pimiento"],
        "bebidas": ["agua", "zumo naranja", "refresco cola"],
    }

    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        return self._scrape_by_terms(category, limit, self._search)

    def _search(self, query: str, limit: int) -> list[ScrapedProduct]:
        params = {
            "query": query,
            "scope": "desktop",
            "lang": "es",
            "rows": limit,
            "start": 0,
        }
        data = self.fetch_json(self.SEARCH_URL, params=params)
        if not data:
            return []

        items = (
            data.get("results", {}).get("items", [])
            or data.get("items", [])
            or data.get("products", [])
        )
        products = []
        for item in items:
            try:
                product = self._parse_item(item, query)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error parseando item: {e}")
        return products

    def _parse_item(self, item: dict, search_query: str) -> Optional[ScrapedProduct]:
        name = (
            item.get("display_name") or item.get("name") or item.get("title", "")
        )
        if not name:
            return None

        price = None
        for key in ("active_price", "price", "current_price", "sale_price"):
            if key in item:
                price = self.parse_price(item[key])
                if price:
                    break
        if not price:
            nested = item.get("prices", {}).get("price")
            if nested:
                price = self.parse_price(nested)
        if not price:
            return None

        external_id = str(
            item.get("id") or item.get("product_id") or item.get("sku", "")
        )
        if not external_id:
            return None

        image_url = item.get("image_url") or item.get("image")
        if isinstance(image_url, dict):
            image_url = image_url.get("url")

        product_url = item.get("url") or item.get("product_url")
        if product_url and not product_url.startswith("http"):
            product_url = self.BASE_URL + product_url

        unit_text = item.get("unit") or item.get("packaging") or ""
        unit_size, unit_type = self.parse_unit(unit_text or name)

        price_per_unit = self.parse_price(item.get("unit_price"))
        if not price_per_unit and unit_size and unit_type in ("kg", "l"):
            price_per_unit = price / unit_size if unit_size > 0 else None

        return ScrapedProduct(
            name=name,
            price=price,
            external_id=external_id,
            supermarket=self.SUPERMARKET_ID,
            brand=item.get("brand"),
            category=search_query,
            image_url=image_url,
            product_url=product_url,
            unit_size=unit_size,
            unit_type=unit_type,
            price_per_unit=price_per_unit,
            in_stock=item.get("in_stock", True),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = CarrefourScraper()
    result = scraper.run(categories=["lacteos", "huevos"], products_per_category=5)
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}")
