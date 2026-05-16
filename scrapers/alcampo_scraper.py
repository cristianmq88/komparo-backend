"""
Scraper de Alcampo.
Alcampo usa Algolia para búsqueda de productos.

Endpoint: https://www.compraonline.alcampo.es/api/v5/products?...

NOTA: Si el endpoint cambia, descúbrelo así:
1. Abrir https://www.compraonline.alcampo.es en Chrome
2. F12 → Network → buscar "leche"
3. Mirar las requests AJAX que salen
"""
import logging
import time
import requests
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
        "bebidas": ["agua mineral"]
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.compraonline.alcampo.es/"
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
            "search_term": query,
            "limit": limit,
            "offset": 0
        }
        
        try:
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT
            )
            
            if response.status_code in (403, 429):
                logger.warning(f"⚠️ Alcampo bloqueando: {response.status_code}")
                return []
            
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"Error: {e}")
            return []
        
        return self._parse_results(data, query)
    
    def _parse_results(self, data: dict, query: str) -> list[ScrapedProduct]:
        products = []
        items = (
            data.get("entities", {}).get("product", {}) 
            or data.get("items", []) 
            or data.get("products", [])
        )
        
        # Si es dict, convertir a lista
        if isinstance(items, dict):
            items = list(items.values())
        
        for item in items:
            try:
                product = self._parse_item(item, query)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error: {e}")
        
        return products
    
    def _parse_item(self, item: dict, search_query: str) -> Optional[ScrapedProduct]:
        # Alcampo estructura típica:
        # {
        #   "retailerProductId": "12345",
        #   "name": "Leche semidesnatada Auchan 1L",
        #   "price": {"current": {"amount": 0.89}},
        #   "image": {"src": "..."},
        #   "brand": "Auchan",
        #   ...
        # }
        
        name = item.get("name") or item.get("title") or item.get("displayName")
        if not name:
            return None
        
        # Precio (suele estar anidado en Alcampo)
        price = None
        price_obj = item.get("price", {})
        
        if isinstance(price_obj, dict):
            # Estructura: price.current.amount
            current = price_obj.get("current", {})
            if isinstance(current, dict):
                price = self.parse_price(str(current.get("amount", "")))
            elif current:
                price = self.parse_price(str(current))
            
            # Fallback
            if not price:
                price = self.parse_price(str(price_obj.get("amount", "")))
        
        if not price:
            return None
        
        external_id = str(
            item.get("retailerProductId") 
            or item.get("id") 
            or item.get("sku", "")
        )
        if not external_id:
            return None
        
        # Precio por kg/L
        price_per_unit = None
        unit_price = item.get("pricePerUnit") or price_obj.get("unitPrice")
        if isinstance(unit_price, dict):
            price_per_unit = self.parse_price(str(unit_price.get("amount", "")))
        elif unit_price:
            price_per_unit = self.parse_price(str(unit_price))
        
        # Imagen
        image = item.get("image", {})
        if isinstance(image, dict):
            image = image.get("src") or image.get("url")
        
        # Tamaño
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
            in_stock=item.get("available", True)
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = AlcampoScraper()
    result = scraper.run(categories=["lacteos"], products_per_category=5)
    
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}")
