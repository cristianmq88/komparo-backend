"""
scrapers/carrefour.py

Usa la API interna de Carrefour (www.carrefour.es/api).
Requiere pasar el código postal de Madrid en los parámetros.
"""
from .base import BaseScraper, ScrapedProduct

BASE = "https://www.carrefour.es/mango/api/v1"

# Categorías principales de Carrefour con sus IDs de API
CATEGORY_IDS = [
    ("frutas-y-verduras",        "Frutas y verduras"),
    ("carnes-y-aves",            "Carnicería"),
    ("pescados-y-mariscos",      "Pescadería"),
    ("lacteos-huevos-y-mantequilla", "Lácteos y huevos"),
    ("charcuteria-y-quesos",     "Charcutería"),
    ("aceites-y-conservas",      "Aceites y conservas"),
    ("pasta-arroz-y-legumbres",  "Pasta, arroz y legumbres"),
    ("panaderia-y-bolleria",     "Panadería"),
    ("bebidas",                  "Bebidas"),
    ("congelados",               "Congelados"),
    ("helados",                  "Helados"),
    ("cereales-y-galletas",      "Cereales y galletas"),
    ("cafes-e-infusiones",       "Café"),
]


class CarrefourScraper(BaseScraper):
    supermarket_id = "carrefour"
    name           = "Carrefour"
    base_url       = BASE

    async def get_categories(self) -> list[dict]:
        return [{"id": cid, "name": name, "parent": ""} for cid, name in CATEGORY_IDS]

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        """
        Endpoint paginado — recorre todas las páginas hasta que no haya más.
        """
        products = []
        page = 0

        while True:
            data = await self._get(
                f"{BASE}/es/search",
                params={
                    "query":       "",
                    "categoryId":  category_id,
                    "lang":        "es",
                    "currentPage": page,
                    "pageSize":    48,
                    "postCode":    self.postal_code,
                }
            )
            results = data.get("products", [])
            if not results:
                break

            for raw in results:
                p = self._parse_product(raw, category_id)
                if p:
                    products.append(p)

            total_pages = data.get("pagination", {}).get("totalPages", 1)
            if page >= total_pages - 1:
                break
            page += 1

        return products

    def _parse_product(self, raw: dict, category: str) -> ScrapedProduct | None:
        try:
            price_data  = raw.get("price", {})
            price       = float(price_data.get("value", 0))
            if price == 0:
                return None

            # precio por unidad de referencia
            ref_info    = raw.get("pricePerUnit", {})
            unit_label  = ref_info.get("formattedValue", "")    # "3,95 €/kg"
            per_unit    = ref_info.get("value")

            # oferta
            was_price   = raw.get("wasPrice", {})
            on_sale     = bool(was_price)
            orig_price  = float(was_price.get("value", 0)) if on_sale else None

            # imagen
            images      = raw.get("images", [])
            image_url   = images[0].get("url", "") if images else ""
            if image_url and not image_url.startswith("http"):
                image_url = "https://www.carrefour.es" + image_url

            # marca blanca
            brand       = raw.get("brandName", "")
            is_own      = brand.lower() in ("carrefour", "simpl", "tex", "carrefour bio")

            return ScrapedProduct(
                external_id    = str(raw.get("code", raw.get("productCode", ""))),
                name           = raw.get("name", ""),
                price          = price,
                price_per_unit = float(per_unit) if per_unit else None,
                unit_label     = unit_label,
                category       = category,
                brand          = brand,
                image_url      = image_url,
                is_own_brand   = is_own,
                is_on_sale     = on_sale,
                original_price = orig_price,
            )
        except Exception:
            return None
