"""
Clase base para todos los scrapers de supermercados.
Define el contrato común que todos deben cumplir.
"""
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests
from requests.adapters import HTTPAdapter

try:  # urllib3 >= 1.26
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    from requests.packages.urllib3.util.retry import Retry

from .proxy import proxy_manager

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Producto raspado de una web de supermercado."""
    name: str
    price: float
    external_id: str
    supermarket: str
    
    # Opcionales
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    unit_type: Optional[str] = None       # 'kg', 'l', 'ud'
    unit_size: Optional[float] = None     # 1, 0.5, 1.5
    price_per_unit: Optional[float] = None  # €/kg, €/L
    in_stock: bool = True
    
    def __post_init__(self):
        # Normalizar el nombre para búsquedas
        self.normalized_name = self._normalize(self.name)
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalizar nombre para matching entre supermercados."""
        text = text.lower().strip()
        # Quitar acentos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        # Quitar caracteres especiales
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Espacios múltiples a uno
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


@dataclass
class ScraperResult:
    """Resultado de ejecutar un scraper."""
    supermarket: str
    products: list[ScrapedProduct] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    
    @property
    def success(self) -> bool:
        return len(self.products) > 0 and len(self.errors) == 0
    
    @property
    def duration_seconds(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0


class BaseScraper(ABC):
    """Clase base que todos los scrapers deben heredar."""
    
    # Configuración por scraper
    SUPERMARKET_ID: str = ""        # Identificador único
    SUPERMARKET_NAME: str = ""      # Nombre legible
    BASE_URL: str = ""              # URL base
    REQUEST_DELAY: float = 1.0      # Segundos entre requests (importante!)
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    # Cabeceras por defecto; cada scraper puede sobreescribir HEADERS.
    HEADERS: dict = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9",
    }

    def __init__(self, postal_code: str = "28001"):
        """
        Args:
            postal_code: Código postal de Madrid por defecto (para súper que lo requieren)
        """
        self.postal_code = postal_code
        self.result = ScraperResult(supermarket=self.SUPERMARKET_ID)
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Sesión HTTP reutilizable con reintentos automáticos y backoff."""
        session = requests.Session()
        retries = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update(self.HEADERS)
        return session

    def fetch(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None,
              **kwargs) -> requests.Response:
        """
        GET con proxy anti-bloqueo y rotación de User-Agent.

        Si hay proxy configurado (ver scrapers/proxy.py) enruta la petición a
        través de él y rota la IP/UA; si no, va directo. Centraliza timeout,
        verificación TLS y reintentos para todos los scrapers.
        """
        kwargs.setdefault("timeout", self.TIMEOUT)

        proxies = proxy_manager.next_proxies()
        if proxies:
            kwargs["proxies"] = proxies
            kwargs.setdefault("verify", proxy_manager.verify)

        # Rotar User-Agent por petición (manteniendo el resto de cabeceras,
        # p. ej. el Referer, que algunos súper exigen).
        req_headers = dict(headers) if headers else {}
        req_headers["User-Agent"] = proxy_manager.random_user_agent()

        return self.session.get(url, params=params, headers=req_headers, **kwargs)
    
    @abstractmethod
    def scrape_category(self, category: str, limit: int = 50) -> list[ScrapedProduct]:
        """
        Cada scraper debe implementar este método.
        
        Args:
            category: Categoría a raspar (ej: 'lacteos', 'panaderia')
            limit: Máximo de productos por categoría
        """
        pass
    
    @abstractmethod
    def get_categories(self) -> list[str]:
        """Devuelve las categorías que sabe raspar este scraper."""
        pass
    
    def run(self, categories: Optional[list[str]] = None, products_per_category: int = 30) -> ScraperResult:
        """
        Ejecuta el scraper completo.
        
        Args:
            categories: Categorías a raspar. Si None, todas.
            products_per_category: Productos por categoría
        """
        logger.info(f"🚀 Iniciando scraper {self.SUPERMARKET_NAME}")
        self.result.started_at = datetime.utcnow()
        
        cats = categories or self.get_categories()
        
        for cat in cats:
            try:
                logger.info(f"  📂 Categoría: {cat}")
                products = self.scrape_category(cat, limit=products_per_category)
                self.result.products.extend(products)
                logger.info(f"     ✅ {len(products)} productos")
                
                # Pausa entre categorías para no saturar
                time.sleep(self.REQUEST_DELAY)
            except Exception as e:
                error_msg = f"Categoría {cat}: {str(e)}"
                logger.error(f"     ❌ {error_msg}")
                self.result.errors.append(error_msg)
        
        self.result.finished_at = datetime.utcnow()
        logger.info(
            f"🏁 {self.SUPERMARKET_NAME} terminado: "
            f"{len(self.result.products)} productos en {self.result.duration_seconds:.1f}s"
        )
        return self.result
    
    @staticmethod
    def parse_price(text: str) -> Optional[float]:
        """Convierte un texto de precio a float. Acepta '1,99 €', '1.99', etc."""
        if not text:
            return None
        # Limpiar el texto
        text = text.strip().replace('€', '').replace(' ', '')
        # Si tiene tanto coma como punto, asumir que coma es decimal
        if ',' in text and '.' in text:
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '.')
        try:
            return float(text)
        except ValueError:
            return None
    
    @staticmethod
    def parse_unit(text: str) -> tuple[Optional[float], Optional[str]]:
        """
        Extrae tamaño y unidad de un texto como '1L', '500g', '6 ud.', '1,5 kg'.
        Devuelve (size, unit) o (None, None) si no se puede parsear.
        """
        if not text:
            return None, None
        
        text = text.lower().strip()
        
        # Patrón: número + unidad
        match = re.search(r'(\d+[,.]?\d*)\s*(kg|g|l|ml|cl|ud|uds|unidades?)', text)
        if match:
            size_str, unit = match.groups()
            size = float(size_str.replace(',', '.'))
            
            # Normalizar unidades
            unit_map = {
                'g': 'g', 'kg': 'kg',
                'ml': 'ml', 'cl': 'cl', 'l': 'l',
                'ud': 'ud', 'uds': 'ud', 'unidad': 'ud', 'unidades': 'ud'
            }
            return size, unit_map.get(unit, unit)
        
        return None, None
