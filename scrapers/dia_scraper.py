"""
Scraper de Dia.

Endpoint: https://www.dia.es/api/v1/search-back/search/products
"""
import logging
from typing import Optional

from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class DiaScraper(BaseScraper):
    SUPERMARKET_ID = "dia"
    SUPERMARKET_NAME = "Dia"
    BASE_URL = "https://www.dia.es"
    REQUEST_DELAY = 2.0

    SEARCH_URL = "https://www.dia.es/api/v1/search-back/search/products"

    CATEGORIES = {
        "lacteos": ["leche", "yogur", "queso"],
        "panaderia": ["pan", "pan molde"],
        "huevos": ["huevos"],
        "carnes": ["pollo", "carne picada"],
        "pescados": ["salmon", "merluza"],
        "aceites": ["aceite oliva"],
        "pasta": ["pasta", "arroz"],
        "frutas": ["platano", "manzana"],
        "verduras": ["patata", "cebolla"],
        "bebidas": ["agua", "refresco"],
    }

    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        return self._scrape_by_terms(category, limit, self._search)

    def _search(self, query: str, limit: int) -> list[ScrapedProduct]:
        params = {"q": query, "size": limit, "page": 0, "sort": "relevance"}
        data = self.fetch_json(self.SEARCH_URL, params=params)
        if not data:
            return []

        items = data.get("hits", []) or data.get("products", [])
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
        name = item.get("name") or item.get("title")
        if not name:
            return None

        price_obj = item.get("price")
        price = None
        if isinstance(price_obj, dict):
            price = self.parse_price(
                price_obj.get("value") or price_obj.get("current")
            )
        elif price_obj is not None:
            price = self.parse_price(price_obj)
        if not price:
            return None

        external_id = str(item.get("id") or item.get("sku", ""))
        if not external_id:
            return None

        price_per_unit = None
        if isinstance(price_obj, dict):
            for key in ("perKg", "perLitre", "perUnit", "reference"):
                if key in price_obj:
                    price_per_unit = self.parse_price(price_obj[key])
                    if price_per_unit:
                        break

        image = item.get("image") or item.get("imageUrl")
        if isinstance(image, dict):
            image = image.get("url") or image.get("href")

        product_url = item.get("url") or item.get("link")
        if product_url and not product_url.startswith("http"):
            product_url = self.BASE_URL + product_url

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
            product_url=product_url,
            unit_size=unit_size,
            unit_type=unit_type,
            price_per_unit=price_per_unit,
            in_stock=item.get("available", True),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = DiaScraper()
    result = scraper.run(categories=["lacteos"], products_per_category=5)
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}")
