"""
Scraper de Dia.
Dia tiene su catálogo accesible vía AJAX en su web.

Endpoint público de búsqueda:
https://www.dia.es/api/v1/search-back/search/products?q=...

Sí, esta es la URL que su web pública usa por debajo.
"""
import logging
import time
import requests
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
        "bebidas": ["agua", "refresco"]
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.dia.es/"
    }
    
    def get_categories(self) -> list[str]:
        return list(self.CATEGORIES.keys())
    
    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        if category not in self.CATEGORIES:
            return []
        
        all_products = []
        terms = self.CATEGORIES[category]
        per_term = max(1, limit // len(terms))
        
        for term in terms:
            try:
                products = self._search(term, limit=per_term)
                all_products.extend(products)
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"  Error buscando '{term}': {e}")
        
        return all_products[:limit]
    
    def _search(self, query: str, limit: int = 10) -> list[ScrapedProduct]:
        params = {
            "q": query,
            "size": limit,
            "page": 0,
            "sort": "relevance"
        }
        
        try:
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT
            )
            
            if response.status_code == 403:
                logger.warning("⚠️ Dia bloqueando")
                return []
            
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"Error: {e}")
            return []
        
        return self._parse_results(data, query)
    
    def _parse_results(self, data: dict, query: str) -> list[ScrapedProduct]:
        products = []
        items = data.get("hits", []) or data.get("products", [])
        
        for item in items:
            try:
                product = self._parse_item(item, query)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error: {e}")
        
        return products
    
    def _parse_item(self, item: dict, search_query: str) -> Optional[ScrapedProduct]:
        # Estructura típica de Dia:
        # {
        #   "id": "123456",
        #   "name": "Leche semidesnatada Dia 1L",
        #   "price": {"value": 0.89, "perKg": 0.89},
        #   "image": "...",
        #   "brand": "Dia",
        #   ...
        # }
        
        name = item.get("name") or item.get("title")
        if not name:
            return None
        
        # Precio
        price = None
        price_obj = item.get("price")
        if isinstance(price_obj, dict):
            price = self.parse_price(str(price_obj.get("value", price_obj.get("current", ""))))
        elif price_obj:
            price = self.parse_price(str(price_obj))
        
        if not price:
            return None
        
        external_id = str(item.get("id") or item.get("sku", ""))
        if not external_id:
            return None
        
        # Precio por kg/L
        price_per_unit = None
        if isinstance(price_obj, dict):
            for key in ["perKg", "perLitre", "perUnit", "reference"]:
                if key in price_obj:
                    price_per_unit = self.parse_price(str(price_obj[key]))
                    if price_per_unit:
                        break
        
        # Imagen
        image = item.get("image") or item.get("imageUrl")
        if isinstance(image, dict):
            image = image.get("url") or image.get("href")
        
        # URL del producto
        product_url = item.get("url") or item.get("link")
        if product_url and not product_url.startswith("http"):
            product_url = self.BASE_URL + product_url
        
        # Tamaño/unidad
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
            in_stock=item.get("available", True)
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = DiaScraper()
    result = scraper.run(categories=["lacteos"], products_per_category=5)
    
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}")
