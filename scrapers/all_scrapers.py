"""
scrapers/alcampo.py — API interna de Alcampo (compraonline.alcampo.es)
"""
from .base import BaseScraper, ScrapedProduct

BASE = "https://www.compraonline.alcampo.es/api/v5"

CATEGORIES = [
    ("OCC10",   "Alimentación"),
    ("OC16",    "Lácteos y huevos"),
    ("OCC20",   "Frutas y verduras"),
    ("OCC30",   "Carnicería y charcutería"),
    ("OCC40",   "Pescadería"),
    ("OC18",    "Aceites y vinagre"),
    ("OCC50",   "Bebidas"),
    ("OCC60",   "Congelados"),
    ("OCC70",   "Desayuno y dulces"),
    ("OCC80",   "Higiene y droguería"),
]


class AlcampoScraper(BaseScraper):
    supermarket_id = "alcampo"
    name           = "Alcampo"

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in CATEGORIES]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        products = []
        offset = 0
        limit  = 50

        while True:
            data = await self._get(
                f"{BASE}/categories/{category_id}/products",
                params={
                    "offset":     offset,
                    "limit":      limit,
                    "postalCode": self.postal_code,
                    "lang":       "es",
                }
            )
            items = data.get("products", data.get("results", []))
            if not items:
                break

            for raw in items:
                p = self._parse(raw, category_id)
                if p:
                    products.append(p)

            total = data.get("total", len(items))
            offset += limit
            if offset >= total:
                break

        return products

    def _parse(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price    = float(raw.get("price", {}).get("value", 0))
            if price == 0:
                return None

            ref      = raw.get("pricePerUnit", {})
            brand    = raw.get("brand", {}).get("name", "") or raw.get("brandName", "")
            is_own   = "alcampo" in brand.lower() or "auchan" in brand.lower()
            on_sale  = raw.get("isPromo", False)
            orig     = raw.get("originalPrice", {}).get("value")

            return ScrapedProduct(
                external_id    = str(raw.get("id", raw.get("sku", ""))),
                name           = raw.get("name", ""),
                price          = price,
                price_per_unit = float(ref.get("value", 0)) or None,
                unit_label     = ref.get("formattedValue", ""),
                category       = category,
                brand          = brand,
                image_url      = (raw.get("images") or [{}])[0].get("url", ""),
                is_own_brand   = is_own,
                is_on_sale     = on_sale,
                original_price = float(orig) if orig else None,
            )
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════

"""
scrapers/dia.py — Scraping web de Dia (usa Playwright para JS)
"""
from .base import BaseScraper, ScrapedProduct

DIA_CATEGORIES = [
    ("frescos/frutas-y-verduras",       "Frutas y verduras"),
    ("frescos/carne-y-charcuteria",     "Carnicería"),
    ("frescos/pescado-y-marisco",       "Pescadería"),
    ("frescos/lacteos-y-huevos",        "Lácteos y huevos"),
    ("alimentacion/aceites-y-conservas","Aceites y conservas"),
    ("alimentacion/pasta-y-arroz",      "Pasta y arroz"),
    ("bebidas",                         "Bebidas"),
    ("congelados",                      "Congelados"),
]


class DiaScraper(BaseScraper):
    supermarket_id = "dia"
    name           = "Dia"
    base_url       = "https://www.dia.es"

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in DIA_CATEGORIES]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        """
        Dia tiene una API JSON en /api/2.0/catalog/search.
        Requiere CP de Madrid y la sesión puede requerir una cookie inicial.
        """
        products = []
        page = 0

        while True:
            data = await self._get(
                f"{self.base_url}/api/2.0/catalog/search",
                params={
                    "category": category_id,
                    "page":     page,
                    "pageSize": 60,
                    "storeId":  "28001",    # tienda Madrid
                    "lang":     "es_ES",
                }
            )
            items = data.get("products", [])
            if not items:
                break

            for raw in items:
                p = self._parse(raw, category_id)
                if p:
                    products.append(p)

            if page >= data.get("totalPages", 1) - 1:
                break
            page += 1

        return products

    def _parse(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price   = float(raw.get("price", {}).get("value", 0))
            if price == 0:
                return None

            brand   = raw.get("brand", "")
            is_own  = brand.lower() in ("dia", "dia%", "basic line")

            ref     = raw.get("pricePerUnit", "")   # "1,99 €/kg"
            per_u   = None
            if ref:
                try:
                    per_u = float(ref.split("€")[0].replace(",", ".").strip())
                except Exception:
                    pass

            return ScrapedProduct(
                external_id    = str(raw.get("code", "")),
                name           = raw.get("name", ""),
                price          = price,
                price_per_unit = per_u,
                unit_label     = ref,
                category       = category,
                brand          = brand,
                image_url      = raw.get("imageUrl", ""),
                is_own_brand   = is_own,
                is_on_sale     = raw.get("potentialPromotions", []) != [],
            )
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════

"""
scrapers/lidl.py — API interna de Lidl
"""
from .base import BaseScraper, ScrapedProduct

LIDL_BASE = "https://www.lidl.es/api/items"

LIDL_CATEGORIES = [
    ("fruta-y-verdura",       "Frutas y verduras"),
    ("carne-y-charcuteria",   "Carnicería"),
    ("pescaderia",            "Pescadería"),
    ("lacteos-y-huevos",      "Lácteos y huevos"),
    ("despensa",              "Despensa"),
    ("bebidas",               "Bebidas"),
    ("congelados",            "Congelados"),
    ("panaderia",             "Panadería"),
]


class LidlScraper(BaseScraper):
    supermarket_id = "lidl"
    name           = "Lidl"

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in LIDL_CATEGORIES]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        products = []
        page = 1

        while True:
            data = await self._get(
                f"{LIDL_BASE}",
                params={
                    "category":   category_id,
                    "page":       page,
                    "size":       50,
                    "region":     "es",
                    "locale":     "es_ES",
                    "storeCode":  "28001",
                }
            )
            items = data.get("gridData", {}).get("items", [])
            if not items:
                break

            for raw in items:
                p = self._parse(raw, category_id)
                if p:
                    products.append(p)

            if not data.get("gridData", {}).get("hasNextPage"):
                break
            page += 1

        return products

    def _parse(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price_raw = raw.get("price", {})
            price     = float(price_raw.get("price", 0))
            if price == 0:
                return None

            ref_str   = raw.get("referencePrice", "")  # "2,99 €/kg"
            per_u     = None
            if ref_str:
                try:
                    per_u = float(ref_str.split("€")[0].replace(",", ".").strip())
                except Exception:
                    pass

            brand     = raw.get("brand", "")
            is_own    = brand.lower() in ("milbona", "mcennedy", "cien", "esmara", "lidl")

            return ScrapedProduct(
                external_id    = str(raw.get("productId", raw.get("id", ""))),
                name           = raw.get("fullTitle", raw.get("title", "")),
                price          = price,
                price_per_unit = per_u,
                unit_label     = ref_str,
                category       = category,
                brand          = brand,
                image_url      = raw.get("imageUrl", ""),
                is_own_brand   = is_own,
                is_on_sale     = raw.get("isDiscounted", False),
                original_price = float(price_raw.get("originalPrice", 0)) or None,
            )
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════

"""
scrapers/ahorramas.py — Scraping web de Ahorramas con Playwright
Ahorramas es la cadena regional madrileña más grande.
Su web requiere JS, por eso usamos Playwright.
"""
import json
from .base import BaseScraper, ScrapedProduct

AH_BASE = "https://www.ahorramas.com"

AH_CATEGORIES = [
    ("/c/frutas-verduras",       "Frutas y verduras"),
    ("/c/carniceria",            "Carnicería"),
    ("/c/pescaderia",            "Pescadería"),
    ("/c/lacteos",               "Lácteos y huevos"),
    ("/c/charcuteria",           "Charcutería"),
    ("/c/aceites-vinagres",      "Aceites"),
    ("/c/pasta-arroz-legumbres", "Pasta y arroz"),
    ("/c/bebidas",               "Bebidas"),
    ("/c/congelados",            "Congelados"),
]


class AhorramasScraper(BaseScraper):
    supermarket_id = "ahorramas"
    name           = "Ahorramas"
    base_url       = AH_BASE

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in AH_CATEGORIES]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        """
        Ahorramas usa una API JSON en /api/catalog.
        Si esta API no estuviera disponible, el fallback es Playwright.
        """
        products = []
        page = 0

        while True:
            try:
                data = await self._get(
                    f"{AH_BASE}/api/catalog/products",
                    params={
                        "category": category_id.lstrip("/"),
                        "page":     page,
                        "pageSize": 50,
                        "cp":       self.postal_code,
                    }
                )
                items = data.get("products", [])
                if not items:
                    break

                for raw in items:
                    p = self._parse(raw, category_id)
                    if p:
                        products.append(p)

                if page >= data.get("totalPages", 1) - 1:
                    break
                page += 1

            except Exception:
                # Fallback: Playwright para renderizar la página
                items = await self._scrape_with_playwright(category_id, page)
                products.extend(items)
                break

        return products

    async def _scrape_with_playwright(self, category_id: str, page: int) -> list[ScrapedProduct]:
        """Fallback con Playwright cuando la API falla"""
        from playwright.async_api import async_playwright
        products = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                locale="es-ES",
                user_agent=self.headers["User-Agent"]
            )
            pg = await ctx.new_page()
            url = f"{AH_BASE}{category_id}?page={page}"
            await pg.goto(url, wait_until="networkidle")
            await pg.wait_for_timeout(2000)

            # Extraer datos del DOM
            items = await pg.evaluate("""
                () => {
                    const cards = document.querySelectorAll('[data-testid="product-card"]');
                    return Array.from(cards).map(card => ({
                        id:    card.dataset.productId || '',
                        name:  card.querySelector('.product-name')?.textContent?.trim() || '',
                        price: parseFloat(card.querySelector('.price-value')?.textContent?.replace(',','.') || 0),
                        ref:   card.querySelector('.price-per-unit')?.textContent?.trim() || '',
                        img:   card.querySelector('img')?.src || '',
                        brand: card.querySelector('.brand')?.textContent?.trim() || '',
                    }));
                }
            """)
            await browser.close()

            for raw in items:
                if raw.get("price", 0) > 0:
                    products.append(ScrapedProduct(
                        external_id    = str(raw["id"]),
                        name           = raw["name"],
                        price          = raw["price"],
                        price_per_unit = None,
                        unit_label     = raw.get("ref", ""),
                        category       = category_id,
                        brand          = raw.get("brand", ""),
                        image_url      = raw.get("img", ""),
                        is_own_brand   = "ahorramas" in raw.get("brand", "").lower(),
                    ))

        return products

    def _parse(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price = float(raw.get("price", 0))
            if price == 0:
                return None
            brand = raw.get("brand", "")
            return ScrapedProduct(
                external_id    = str(raw.get("id", "")),
                name           = raw.get("name", ""),
                price          = price,
                price_per_unit = raw.get("pricePerUnit"),
                unit_label     = raw.get("pricePerUnitLabel", ""),
                category       = category,
                brand          = brand,
                image_url      = raw.get("imageUrl", ""),
                is_own_brand   = "ahorramas" in brand.lower() or "bosque verde" in brand.lower(),
                is_on_sale     = raw.get("hasDiscount", False),
            )
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════

"""
scrapers/aldi.py — API interna de Aldi España
"""
from .base import BaseScraper, ScrapedProduct

ALDI_BASE = "https://www.aldi.es/content/aldi-es/es"

ALDI_CATEGORIES = [
    ("frutas-y-verduras",    "Frutas y verduras"),
    ("carne-y-aves",         "Carnicería"),
    ("pescado",              "Pescadería"),
    ("lacteos-y-huevos",     "Lácteos y huevos"),
    ("despensa",             "Despensa"),
    ("bebidas",              "Bebidas"),
    ("congelados",           "Congelados"),
    ("panaderia",            "Panadería"),
]


class AldiScraper(BaseScraper):
    supermarket_id = "aldi"
    name           = "Aldi"

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in ALDI_CATEGORIES]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        """
        Aldi expone sus productos en formato JSON-LD dentro del HTML.
        Usamos su API de búsqueda cuando está disponible.
        """
        products = []
        page = 1

        while True:
            data = await self._get(
                f"https://www.aldi.es/api/products",
                params={
                    "category": category_id,
                    "page":     page,
                    "size":     48,
                    "region":   "es",
                }
            )
            items = data.get("products", data.get("items", []))
            if not items:
                break

            for raw in items:
                p = self._parse(raw, category_id)
                if p:
                    products.append(p)

            if not data.get("hasMore", False):
                break
            page += 1

        return products

    def _parse(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price   = float(raw.get("price", raw.get("regularPrice", 0)))
            if price == 0:
                return None

            ref     = raw.get("pricePerUnit", "")
            per_u   = None
            if ref:
                try:
                    per_u = float(str(ref).split("€")[0].replace(",", ".").strip())
                except Exception:
                    pass

            brand   = raw.get("brand", raw.get("manufacturer", ""))
            is_own  = brand.lower() in (
                "milbona", "mcennedy", "cien", "specially selected",
                "aldi", "grandessa", "cucina nobile"
            )

            return ScrapedProduct(
                external_id    = str(raw.get("id", raw.get("ean", ""))),
                name           = raw.get("name", raw.get("title", "")),
                price          = price,
                price_per_unit = per_u,
                unit_label     = str(ref) if ref else None,
                category       = category,
                brand          = brand,
                image_url      = raw.get("image", raw.get("imageUrl", "")),
                is_own_brand   = is_own,
                is_on_sale     = raw.get("isSpecialBuy", False),
                original_price = float(raw.get("originalPrice", 0)) or None,
            )
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════

"""
scrapers/corteingles.py — API interna de El Corte Inglés / Supercor
"""
from .base import BaseScraper, ScrapedProduct

ECI_BASE = "https://www.elcorteingles.es/supermercado/api"

ECI_CATEGORIES = [
    ("frutas-y-verduras",        "Frutas y verduras"),
    ("carne-y-charcuteria",      "Carnicería y charcutería"),
    ("pescado-y-marisco",        "Pescadería"),
    ("lacteos-y-derivados",      "Lácteos y huevos"),
    ("aceites-y-conservas",      "Aceites y conservas"),
    ("pasta-arroz-y-legumbres",  "Pasta, arroz y legumbres"),
    ("bebidas",                  "Bebidas"),
    ("congelados",               "Congelados"),
    ("cafes-e-infusiones",       "Café"),
]


class CorteInglesScraper(BaseScraper):
    supermarket_id = "corteingles"
    name           = "El Corte Inglés"

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in ECI_CATEGORIES]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        products = []
        page = 1

        while True:
            data = await self._get(
                f"{ECI_BASE}/products",
                params={
                    "category":   category_id,
                    "page":       page,
                    "pageSize":   60,
                    "storeId":    "010202",    # tienda Madrid centro
                    "postalCode": self.postal_code,
                    "lang":       "es",
                }
            )
            items = data.get("products", [])
            if not items:
                break

            for raw in items:
                p = self._parse(raw, category_id)
                if p:
                    products.append(p)

            if page >= data.get("totalPages", 1):
                break
            page += 1

        return products

    def _parse(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price_info = raw.get("prices", {})
            price      = float(price_info.get("finalPrice", price_info.get("price", 0)))
            if price == 0:
                return None

            ref        = price_info.get("priceByUnit", {})
            per_u      = float(ref.get("value", 0)) or None
            unit_label = ref.get("formattedValue", "")

            on_sale    = price_info.get("hasDiscount", False)
            orig       = float(price_info.get("originalPrice", 0)) or None

            brand      = raw.get("brand", {}).get("name", "") if isinstance(raw.get("brand"), dict) else raw.get("brand", "")
            is_own     = brand.lower() in ("el corte inglés", "aliada", "supercor")

            imgs       = raw.get("images", [])
            image_url  = imgs[0].get("url", "") if imgs else ""

            return ScrapedProduct(
                external_id    = str(raw.get("code", raw.get("id", ""))),
                name           = raw.get("name", ""),
                price          = price,
                price_per_unit = per_u,
                unit_label     = unit_label,
                category       = category,
                brand          = brand,
                image_url      = image_url,
                is_own_brand   = is_own,
                is_on_sale     = on_sale,
                original_price = orig,
            )
        except Exception:
            return None
