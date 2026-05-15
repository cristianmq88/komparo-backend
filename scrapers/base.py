"""
scrapers/base.py — Clase base abstracta para todos los scrapers

Cada supermercado hereda de esta clase e implementa los métodos abstractos.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
ua = UserAgent()

MADRID_POSTAL_CODE = "28001"


@dataclass
class ScrapedProduct:
    """Producto tal como llega del scraper, antes de guardar en BD"""
    external_id:    str
    name:           str
    price:          float
    price_per_unit: Optional[float]
    unit_label:     Optional[str]        # "€/kg", "€/L", "€/ud"
    category:       str
    subcategory:    str = ""
    brand:          str = ""
    image_url:      str = ""
    unit:           str = "ud"           # kg, L, ud, g
    unit_size:      Optional[float] = None
    is_own_brand:   bool = False
    is_on_sale:     bool = False
    original_price: Optional[float] = None
    scraped_at:     datetime = field(default_factory=datetime.utcnow)


class BaseScraper(ABC):
    """
    Clase base para todos los scrapers.

    Cada subclase implementa:
    - get_categories() → lista de categorías a scrapear
    - scrape_category(category_id) → lista de ScrapedProduct
    """

    supermarket_id: str = ""
    name:           str = ""
    base_url:       str = ""
    postal_code:    str = MADRID_POSTAL_CODE

    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": ua.random,
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept": "application/json, text/html",
        }

    @abstractmethod
    async def get_categories(self) -> list[dict]:
        """
        Retorna lista de categorías disponibles.
        Formato: [{"id": "...", "name": "...", "parent": "..."}]
        """

    @abstractmethod
    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        """Extrae todos los productos de una categoría"""

    async def scrape_all(self) -> list[ScrapedProduct]:
        """Scrapea todas las categorías y devuelve todos los productos"""
        all_products = []
        categories = await self.get_categories()
        logger.info(f"[{self.name}] Scrapeando {len(categories)} categorías")

        for cat in categories:
            try:
                products = await self.scrape_category(cat["id"])
                all_products.extend(products)
                logger.info(f"[{self.name}] {cat['name']}: {len(products)} productos")
                await asyncio.sleep(1.5)   # pausa respetuosa entre peticiones
            except Exception as e:
                logger.error(f"[{self.name}] Error en categoría {cat['id']}: {e}")

        logger.info(f"[{self.name}] Total: {len(all_products)} productos")
        return all_products

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _get(self, url: str, params: dict = None, headers: dict = None) -> dict:
        """GET con reintentos automáticos"""
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                params=params,
                headers={**self.headers, **(headers or {})}
            )
            resp.raise_for_status()
            return resp.json()
