"""
Scraper de Carrefour.
USA SU API PÚBLICA OFICIAL → es legal, rápido y estable.

Endpoint público: 
https://www.carrefour.es/cobertura-ecommerce/api/v1/...

Y para productos:
https://www.carrefour.es/search-api/query/v1/search?query=...
"""
import logging
import time
import requests
from typing import Optional

from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class CarrefourScraper(BaseScraper):
    SUPERMARKET_ID = "carrefour"
    SUPERMARKET_NAME = "Carrefour"
    BASE_URL = "https://www.carrefour.es"
    REQUEST_DELAY = 1.5
    
    # Endpoint público de búsqueda
    SEARCH_URL = "https://www.carrefour.es/search-api/query/v1/search"
    
    # Categorías → palabras de búsqueda
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
        "bebidas": ["agua", "zumo naranja", "refresco cola"]
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.carrefour.es/"
    }
    
    def get_categories(self) -> list[str]:
        return list(self.CATEGORIES.keys())
    
    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        if category not in self.CATEGORIES:
            logger.warning(f"Categoría desconocida: {category}")
            return []
        
        all_products = []
        search_terms = self.CATEGORIES[category]
        
        # Repartir el límite entre los términos de búsqueda
        per_term = max(1, limit // len(search_terms))
        
        for term in search_terms:
            try:
                products = self._search(term, limit=per_term)
                all_products.extend(products)
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"  Error buscando '{term}': {e}")
        
        return all_products[:limit]
    
    def _search(self, query: str, limit: int = 10) -> list[ScrapedProduct]:
        """Busca productos por término."""
        params = {
            "query": query,
            "scope": "desktop",
            "lang": "es",
            "rows": limit,
            "start": 0
        }
        
        try:
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request fallido: {e}")
            return []
        except ValueError as e:
            logger.error(f"JSON inválido: {e}")
            return []
        
        # Parsear respuesta
        return self._parse_search_results(data, query)
    
    def _parse_search_results(self, data: dict, query: str) -> list[ScrapedProduct]:
        """Convierte la respuesta JSON en ScrapedProducts."""
        products = []
        
        # La estructura es: data["results"]["items"] o similar
        items = (
            data.get("results", {}).get("items", [])
            or data.get("items", [])
            or data.get("products", [])
        )
        
        for item in items:
            try:
                product = self._parse_item(item, query)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error parseando item: {e}")
        
        return products
    
    def _parse_item(self, item: dict, search_query: str) -> Optional[ScrapedProduct]:
        """Convierte un item JSON de Carrefour en ScrapedProduct."""
        # Extraer campos (puede variar según la versión de la API)
        name = (
            item.get("display_name") 
            or item.get("name") 
            or item.get("title", "")
        )
        if not name:
            return None
        
        # Precio (puede venir en distintas formas)
        price = None
        for key in ["active_price", "price", "current_price", "sale_price"]:
            if key in item:
                price = self.parse_price(str(item[key]))
                if price:
                    break
        
        if not price:
            # A veces viene anidado
            price_obj = item.get("prices", {}).get("price")
            if price_obj:
                price = self.parse_price(str(price_obj))
        
        if not price:
            return None
        
        # ID externo
        external_id = str(
            item.get("id") 
            or item.get("product_id") 
            or item.get("sku", "")
        )
        if not external_id:
            return None
        
        # Datos adicionales
        image_url = item.get("image_url") or item.get("image", {}).get("url")
        if isinstance(image_url, dict):
            image_url = image_url.get("url")
        
        # URL del producto
        product_url = item.get("url") or item.get("product_url")
        if product_url and not product_url.startswith("http"):
            product_url = self.BASE_URL + product_url
        
        # Tamaño y unidad
        unit_text = item.get("unit") or item.get("packaging") or ""
        unit_size, unit_type = self.parse_unit(unit_text or name)
        
        # Precio por unidad
        price_per_unit = None
        if item.get("unit_price"):
            price_per_unit = self.parse_price(str(item["unit_price"]))
        elif unit_size and unit_type in ["kg", "l"]:
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
            in_stock=item.get("in_stock", True)
        )


if __name__ == "__main__":
    # Para test local
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = CarrefourScraper()
    result = scraper.run(categories=["lacteos", "huevos"], products_per_category=5)
    
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}")
