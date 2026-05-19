"""
Clase base para todos los scrapers de supermercados.
Define el contrato común que todos deben cumplir.
"""
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9",
}


_ACCENT_MAP = str.maketrans("áéíóúñü", "aeiounu")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_MULTI_SPACE = re.compile(r"\s+")
_UNIT_PATTERN = re.compile(
    r"(\d+[,.]?\d*)\s*(kg|g|l|ml|cl|ud|uds|unidades?|unidad)"
)
_UNIT_MAP = {
    "g": "g", "kg": "kg",
    "ml": "ml", "cl": "cl", "l": "l",
    "ud": "ud", "uds": "ud", "unidad": "ud", "unidades": "ud",
}


def normalize_text(text: str) -> str:
    """Normaliza un nombre para matching cross-supermercado."""
    text = text.lower().strip().translate(_ACCENT_MAP)
    text = _NON_ALNUM.sub("", text)
    return _MULTI_SPACE.sub(" ", text).strip()


@dataclass
class ScrapedProduct:
    """Producto raspado de una web de supermercado."""
    name: str
    price: float
    external_id: str
    supermarket: str

    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    unit_type: Optional[str] = None       # 'kg', 'l', 'ud'
    unit_size: Optional[float] = None
    price_per_unit: Optional[float] = None
    in_stock: bool = True

    normalized_name: str = field(init=False)

    def __post_init__(self):
        self.normalized_name = normalize_text(self.name)


@dataclass
class ScraperResult:
    """Resultado de ejecutar un scraper."""
    supermarket: str
    products: list[ScrapedProduct] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None

    @property
    def success(self) -> bool:
        return bool(self.products) and not self.errors

    @property
    def duration_seconds(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0.0


class BaseScraper(ABC):
    """Clase base que todos los scrapers deben heredar."""

    SUPERMARKET_ID: str = ""
    SUPERMARKET_NAME: str = ""
    BASE_URL: str = ""
    REQUEST_DELAY: float = 1.0
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    EXTRA_HEADERS: dict = {}

    # Subclases pueden definir CATEGORIES como dict[str, list[str|int]].
    CATEGORIES: dict = {}

    def __init__(self, postal_code: str = "28001"):
        self.postal_code = postal_code
        self.result = ScraperResult(supermarket=self.SUPERMARKET_ID)
        self.session = requests.Session()
        headers = dict(DEFAULT_HEADERS)
        if self.BASE_URL:
            headers["Referer"] = self.BASE_URL.rstrip("/") + "/"
        headers.update(self.EXTRA_HEADERS)
        self.session.headers.update(headers)

    # ── API que las subclases pueden reutilizar ──────────────────────────

    def get_categories(self) -> list[str]:
        return list(self.CATEGORIES.keys())

    def fetch_json(
        self, url: str, params: Optional[dict] = None
    ) -> Optional[dict]:
        """GET → JSON con manejo unificado de errores y bloqueos."""
        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            if response.status_code in (403, 429):
                logger.warning(
                    f"⚠️ {self.SUPERMARKET_NAME} bloqueando: {response.status_code}"
                )
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request fallido ({url}): {e}")
        except ValueError as e:
            logger.error(f"JSON inválido ({url}): {e}")
        return None

    def _scrape_by_terms(
        self,
        category: str,
        limit: int,
        search_fn: Callable[[object, int], list[ScrapedProduct]],
    ) -> list[ScrapedProduct]:
        """Helper común para scrapers basados en términos de búsqueda."""
        if category not in self.CATEGORIES:
            logger.warning(f"Categoría desconocida: {category}")
            return []

        terms = self.CATEGORIES[category]
        per_term = max(1, limit // len(terms))
        all_products: list[ScrapedProduct] = []

        for term in terms:
            try:
                products = search_fn(term, per_term)
                all_products.extend(products)
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                logger.error(f"  Error buscando '{term}': {e}")

        return all_products[:limit]

    # ── Contrato abstracto ───────────────────────────────────────────────

    @abstractmethod
    def scrape_category(self, category: str, limit: int = 50) -> list[ScrapedProduct]:
        ...

    # ── Orquestación ─────────────────────────────────────────────────────

    def run(
        self,
        categories: Optional[list[str]] = None,
        products_per_category: int = 30,
    ) -> ScraperResult:
        logger.info(f"🚀 Iniciando scraper {self.SUPERMARKET_NAME}")
        self.result.started_at = datetime.now(timezone.utc)

        for cat in categories or self.get_categories():
            try:
                logger.info(f"  📂 Categoría: {cat}")
                products = self.scrape_category(cat, limit=products_per_category)
                self.result.products.extend(products)
                logger.info(f"     ✅ {len(products)} productos")
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                msg = f"Categoría {cat}: {e}"
                logger.error(f"     ❌ {msg}")
                self.result.errors.append(msg)

        self.result.finished_at = datetime.now(timezone.utc)
        logger.info(
            f"🏁 {self.SUPERMARKET_NAME}: {len(self.result.products)} productos "
            f"en {self.result.duration_seconds:.1f}s"
        )
        return self.result

    # ── Helpers de parsing ───────────────────────────────────────────────

    @staticmethod
    def parse_price(text) -> Optional[float]:
        """Convierte '1,99 €', '1.99', 1.99 → float."""
        if text is None:
            return None
        text = str(text).strip().replace("€", "").replace(" ", "")
        if not text:
            return None
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def parse_unit(text: str) -> tuple[Optional[float], Optional[str]]:
        """Extrae (size, unit) de '500g', '1,5 kg', '6 ud.', etc."""
        if not text:
            return None, None
        match = _UNIT_PATTERN.search(text.lower())
        if not match:
            return None, None
        size_str, unit = match.groups()
        size = float(size_str.replace(",", "."))
        return size, _UNIT_MAP.get(unit, unit)
