"""
Scraper de Mercadona.
Mercadona NO tiene API oficial, pero su web "Mi Mercadona" usa una API interna.

⚠️ ADVERTENCIA:
- Mercadona puede bloquear este endpoint si detecta uso masivo
- Si te bloquean: usar proxies rotativos (ScraperAPI, BrightData)
- En el futuro migrar a Apify (que ya tiene scrapers anti-bloqueo)

Endpoints conocidos:
- Búsqueda: https://tienda.mercadona.es/api/v1_1/categories/...
- Producto: https://tienda.mercadona.es/api/products/{id}/

Mercadona requiere código postal para devolver precios (varían por zona).
"""
import logging
import time
import requests
from typing import Optional

from .base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class MercadonaScraper(BaseScraper):
    SUPERMARKET_ID = "mercadona"
    SUPERMARKET_NAME = "Mercadona"
    BASE_URL = "https://tienda.mercadona.es"
    REQUEST_DELAY = 2.5  # Más lento para no ser bloqueado
    
    # IDs de categorías reales de Mercadona (descubiertos vía DevTools de la web)
    # Estos pueden cambiar. Si cambian, hay que actualizarlos.
    CATEGORIES = {
        "lacteos": [112, 113, 114, 115, 116],  # Leches, yogures, quesos
        "panaderia": [157, 158, 159],          # Panes, biscotes
        "huevos": [134],
        "carnes": [200, 201, 202, 203],        # Pollo, vacuno, cerdo
        "pescados": [212, 213, 214],           # Fresco, congelado
        "aceites": [177, 178],
        "pasta": [142, 143, 144],
        "frutas": [109, 110],
        "verduras": [108],
        "bebidas": [183, 184, 185]
    }
    
    def __init__(self, postal_code: str = "28001"):
        super().__init__(postal_code)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "es-ES,es;q=0.9",
            "Referer": "https://tienda.mercadona.es/"
        }
    
    def get_categories(self) -> list[str]:
        return list(self.CATEGORIES.keys())
    
    def scrape_category(self, category: str, limit: int = 30) -> list[ScrapedProduct]:
        if category not in self.CATEGORIES:
            return []
        
        all_products = []
        category_ids = self.CATEGORIES[category]
        per_cat = max(1, limit // len(category_ids))
        
        for cat_id in category_ids:
            try:
                products = self._fetch_category(cat_id, limit=per_cat)
                all_products.extend(products)
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"  Error en categoría {cat_id}: {e}")
        
        return all_products[:limit]
    
    def _fetch_category(self, category_id: int, limit: int = 10) -> list[ScrapedProduct]:
        """Obtiene productos de una categoría por su ID interno de Mercadona."""
        url = f"{self.BASE_URL}/api/categories/{category_id}/"
        params = {"wh": "mad1"}  # Warehouse Madrid 1 (ajustar si hace falta)
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.TIMEOUT
            )
            
            # Si bloquean, suele venir 403 o 429
            if response.status_code in (403, 429):
                logger.warning(f"⚠️ Mercadona bloqueando: status {response.status_code}")
                return []
            
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request fallido: {e}")
            return []
        except ValueError:
            logger.error("JSON inválido")
            return []
        
        return self._parse_category(data, limit)
    
    def _parse_category(self, data: dict, limit: int) -> list[ScrapedProduct]:
        """Parsea la respuesta de una categoría."""
        products = []
        
        # Mercadona devuelve los productos en 'categories' (subcategorías) o directamente
        items = []
        
        # Estructura observada: data["categories"][i]["products"]
        if "categories" in data:
            for subcat in data["categories"]:
                items.extend(subcat.get("products", []))
        elif "products" in data:
            items = data["products"]
        
        for item in items[:limit]:
            try:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error parseando: {e}")
        
        return products
    
    def _parse_product(self, item: dict) -> Optional[ScrapedProduct]:
        """Convierte un producto JSON de Mercadona en ScrapedProduct."""
        # Estructura de Mercadona:
        # {
        #   "id": "12345",
        #   "display_name": "Leche semidesnatada Hacendado",
        #   "price_instructions": {
        #     "unit_price": "1.05",
        #     "reference_price": "1.05",
        #     "reference_format": "€/l"
        #   },
        #   "thumbnail": "https://prod-mercadona.imgix.net/...",
        #   "share_url": "/product/...",
        #   ...
        # }
        
        name = item.get("display_name") or item.get("name")
        if not name:
            return None
        
        price_info = item.get("price_instructions", {})
        price = self.parse_price(str(price_info.get("unit_price", "")))
        if not price:
            return None
        
        external_id = str(item.get("id", ""))
        if not external_id:
            return None
        
        # Precio por unidad (€/kg, €/L)
        ref_price = price_info.get("reference_price")
        price_per_unit = self.parse_price(str(ref_price)) if ref_price else None
        
        # Tipo de unidad de referencia
        ref_format = price_info.get("reference_format", "")
        unit_type = None
        if "kg" in ref_format.lower():
            unit_type = "kg"
        elif "l" in ref_format.lower():
            unit_type = "l"
        
        # Tamaño del envase
        size_text = item.get("size_format") or item.get("packaging") or ""
        unit_size, parsed_unit = self.parse_unit(size_text or name)
        if not unit_type and parsed_unit:
            unit_type = parsed_unit
        
        share_url = item.get("share_url", "")
        product_url = self.BASE_URL + share_url if share_url and not share_url.startswith("http") else share_url
        
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
            in_stock=not item.get("unavailable_from", None)
        )
    
    @staticmethod
    def _guess_brand(name: str) -> Optional[str]:
        """Mercadona suele usar Hacendado para marca blanca."""
        if "hacendado" in name.lower():
            return "Hacendado"
        if "deliplus" in name.lower():
            return "Deliplus"
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    scraper = MercadonaScraper()
    result = scraper.run(categories=["lacteos"], products_per_category=10)
    
    print(f"\n📊 {result.supermarket}: {len(result.products)} productos\n")
    for p in result.products[:10]:
        print(f"  💰 {p.price:>6.2f}€  {p.name[:50]}  ({p.brand or 'sin marca'})")
