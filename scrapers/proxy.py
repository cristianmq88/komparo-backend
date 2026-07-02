"""
Capa de proxy anti-bloqueo para los scrapers.

Permite enrutar las peticiones a través de un servicio de proxy rotativo para
evitar bloqueos por IP de los supermercados. Se configura por entorno y, si no
hay nada configurado, los scrapers funcionan en modo directo (sin proxy).

Modos soportados (por orden de prioridad):

1. ScraperAPI (gateway, rota IP en el servidor):
     SCRAPERAPI_KEY=tu_api_key
     SCRAPERAPI_COUNTRY=es        (opcional, por defecto es)
     SCRAPERAPI_RENDER=false      (opcional, "true" ejecuta JS)

2. Proxy único / gateway rotativo (BrightData, Smartproxy, Oxylabs…):
     SCRAPER_PROXY_URL=http://usuario:password@gateway.proveedor.com:22225

3. Lista de proxies con rotación local (round-robin):
     SCRAPER_PROXIES=http://u:p@ip1:port,http://u:p@ip2:port,...

Otras variables:
   SCRAPER_PROXY_VERIFY=false     Desactiva verificación TLS (necesario en
                                  algunos gateways como ScraperAPI). Por defecto
                                  se desactiva automáticamente con ScraperAPI.
"""
import itertools
import logging
import os
import random
import threading

logger = logging.getLogger(__name__)


# User-Agents reales para rotar y parecer tráfico de navegadores distintos.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]


def _flag(value: str) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _build_scraperapi_url() -> str | None:
    key = os.getenv("SCRAPERAPI_KEY")
    if not key:
        return None
    # El usuario del proxy admite opciones tipo "scraperapi.country_code=es".
    opts = []
    country = os.getenv("SCRAPERAPI_COUNTRY", "es")
    if country:
        opts.append(f"country_code={country}")
    if _flag(os.getenv("SCRAPERAPI_RENDER", "")):
        opts.append("render=true")
    username = ".".join(["scraperapi", *opts]) if opts else "scraperapi"
    return f"http://{username}:{key}@proxy-server.scraperapi.com:8001"


def _build_proxy_list() -> list[str]:
    """Devuelve la lista de URLs de proxy según la configuración de entorno."""
    scraperapi = _build_scraperapi_url()
    if scraperapi:
        logger.info("🛡️ Proxy anti-bloqueo: ScraperAPI")
        return [scraperapi]

    single = os.getenv("SCRAPER_PROXY_URL")
    if single:
        logger.info("🛡️ Proxy anti-bloqueo: gateway único")
        return [single.strip()]

    multiple = os.getenv("SCRAPER_PROXIES")
    if multiple:
        proxies = [p.strip() for p in multiple.split(",") if p.strip()]
        if proxies:
            logger.info(f"🛡️ Proxy anti-bloqueo: {len(proxies)} proxies con rotación")
            return proxies

    return []


class ProxyManager:
    """Gestiona la rotación de proxies y de User-Agent. Thread-safe."""

    def __init__(self):
        self.proxies = _build_proxy_list()
        self._lock = threading.Lock()
        self._cycle = itertools.cycle(self.proxies) if self.proxies else None

        # Verificación TLS: ScraperAPI requiere desactivarla; por defecto
        # se desactiva si usamos ScraperAPI, salvo override explícito.
        verify_env = os.getenv("SCRAPER_PROXY_VERIFY")
        if verify_env is not None:
            self.verify = _flag(verify_env)
        else:
            self.verify = not bool(os.getenv("SCRAPERAPI_KEY"))

    @property
    def enabled(self) -> bool:
        return bool(self.proxies)

    def next_proxies(self) -> dict | None:
        """Siguiente proxy en formato dict para requests (http+https), o None."""
        if not self._cycle:
            return None
        with self._lock:
            url = next(self._cycle)
        return {"http": url, "https": url}

    @staticmethod
    def random_user_agent() -> str:
        return random.choice(USER_AGENTS)


# Instancia compartida por todos los scrapers.
proxy_manager = ProxyManager()

# Si el gateway exige TLS sin verificar, evitamos llenar los logs de avisos.
if proxy_manager.enabled and not proxy_manager.verify:
    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:  # pragma: no cover
        pass
