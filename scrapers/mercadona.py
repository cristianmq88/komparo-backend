"""
scrapers/mercadona.py

Usa la API interna de Mercadona (tienda.mercadona.es/api).
Es la más limpia y documentada de todas: devuelve JSON estructurado
sin necesidad de Playwright ni cookies especiales.
El código postal de Madrid (28001) se pasa en la cabecera para obtener
precios de la zona Madrid.
"""
import asyncio
from .base import BaseScraper, ScrapedProduct

BASE = "https://tienda.mercadona.es/api"


class MercadonaScraper(BaseScraper):
    supermarket_id = "mercadona"
    name           = "Mercadona"
    base_url       = BASE

    # Mercadona usa el CP en las cabeceras para personalizar precios
    @property
    def _madrid_headers(self):
        return {
            **self.headers,
            "Postal-Code": self.postal_code,  # 28001 = Madrid centro
        }

    async def get_categories(self) -> list[dict]:
        """
        /api/categories/ devuelve el árbol completo de categorías.
        Ejemplo de respuesta:
        {
          "results": [
            { "id": 1, "name": "Lácteos y huevos",
              "categories": [
                { "id": 101, "name": "Leche" }, ...
              ]
            }, ...
          ]
        }
        """
        data = await self._get(f"{BASE}/categories/", headers=self._madrid_headers)
        cats = []
        for parent in data.get("results", []):
            for child in parent.get("categories", []):
                cats.append({
                    "id":     str(child["id"]),
                    "name":   child["name"],
                    "parent": parent["name"],
                })
        return cats

    async def scrape_category(self, category_id: str) -> list[ScrapedProduct]:
        """
        /api/categories/{id}/ devuelve los productos de esa categoría.
        """
        data = await self._get(
            f"{BASE}/categories/{category_id}/",
            headers=self._madrid_headers
        )
        products = []
        for section in data.get("categories", []):
            for raw in section.get("products", []):
                p = self._parse_product(raw, section.get("name", ""))
                if p:
                    products.append(p)
        return products

    def _parse_product(self, raw: dict, subcategory: str) -> ScrapedProduct | None:
        try:
            price_info = raw.get("price_instructions", {})
            price      = float(price_info.get("unit_price", 0))
            if price == 0:
                return None

            # precio por kg/L/ud
            bulk_price  = price_info.get("bulk_price")
            unit_name   = price_info.get("price_decreased_label") or ""
            unit_size   = price_info.get("unit_size")
            size_format = price_info.get("size_format", "")     # "kg", "L", "ud"

            # label tipo "€/kg"
            reference   = price_info.get("reference_price")
            ref_format  = price_info.get("reference_format", "")
            unit_label  = f"€/{ref_format}" if ref_format else None

            display     = raw.get("display_data", {})
            photo_list  = raw.get("photos", [])
            image       = photo_list[0].get("regular", "") if photo_list else ""

            # marca blanca = marca "Hacendado"
            brand       = display.get("brand", "")
            is_own      = brand.lower() in ("hacendado", "deliplus", "bosque verde", "compy")

            return ScrapedProduct(
                external_id    = str(raw["id"]),
                name           = raw.get("display_name", raw.get("slug", "")),
                price          = price,
                price_per_unit = float(reference) if reference else None,
                unit_label     = unit_label,
                category       = raw.get("categories", [{}])[0].get("name", "General") if raw.get("categories") else "General",
                subcategory    = subcategory,
                brand          = brand,
                image_url      = image,
                unit           = size_format or "ud",
                unit_size      = float(unit_size) if unit_size else None,
                is_own_brand   = is_own,
                is_on_sale     = price_info.get("is_new", False),
            )
        except Exception:
            return None
