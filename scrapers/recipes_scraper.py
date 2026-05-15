"""
scrapers/recipes_scraper.py
Extrae recetas de las webs de recetas más populares en España y crea una BD local.
Se ejecuta una vez al mes para actualizar el catálogo.
"""
import asyncio
import json
from typing import Optional
import httpx
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════

RECIPE_SOURCES = {
    "recetasderechupete": {
        "base_url": "https://www.recetasderechupete.com",
        "categories": [
            "/recetas/platos-principales/",
            "/recetas/verduras-y-legumbres/",
            "/recetas/pescados-y-mariscos/",
            "/recetas/carnes/",
            "/recetas/salsas/",
            "/recetas/postres/",
            "/recetas/desayunos/",
        ],
    },
    "cocina.es": {
        "base_url": "https://www.cocina.es",
        "categories": [
            "/recetas/platos-principales/",
            "/recetas/verduras-y-legumbres/",
            "/recetas/pescados/",
            "/recetas/carnes/",
            "/recetas/salsas/",
            "/recetas/postres/",
        ],
    },
    "directo_al_paladar": {
        "base_url": "https://www.directoalpaladar.com",
        "categories": [
            "/recetas/platos-principales/",
            "/recetas/verduras-hortalizas/",
            "/recetas/pescados-mariscos/",
            "/recetas/carnes/",
            "/recetas/postres/",
        ],
    },
    "gastronom_kitchen": {
        "base_url": "https://www.gastronomiaycia.com",
        "categories": [
            "/recetas/platos-principales/",
            "/recetas/verduras/",
            "/recetas/pescados/",
            "/recetas/carnes/",
            "/recetas/salsas/",
            "/recetas/postres/",
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# MODELOS DE RECETAS
# ══════════════════════════════════════════════════════════════════════════════

class Ingredient:
    def __init__(self, name: str, quantity: Optional[str] = None, unit: Optional[str] = None):
        self.name = name.lower().strip()
        self.quantity = quantity
        self.unit = unit or ""

    def to_dict(self):
        return {"name": self.name, "quantity": self.quantity, "unit": self.unit}

    def __repr__(self):
        return f"{self.quantity} {self.unit} {self.name}".strip()


class Recipe:
    def __init__(
        self,
        title: str,
        source: str,
        url: str,
        ingredients: list[Ingredient],
        servings: int = 4,
        difficulty: str = "media",
        time_minutes: Optional[int] = None,
        category: str = "general",
        description: str = "",
        image_url: str = "",
    ):
        self.id = f"{source}_{title.lower().replace(' ', '_')}"
        self.title = title
        self.source = source
        self.url = url
        self.ingredients = ingredients
        self.servings = servings
        self.difficulty = difficulty
        self.time_minutes = time_minutes
        self.category = category
        self.description = description
        self.image_url = image_url

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "servings": self.servings,
            "difficulty": self.difficulty,
            "time_minutes": self.time_minutes,
            "category": self.category,
            "description": self.description,
            "image_url": self.image_url,
        }

    def match_score(self, shopping_items: list[str]) -> float:
        """
        Calcula qué porcentaje de ingredientes de la receta están en la lista de la compra.
        Score 1.0 = todos los ingredientes disponibles.
        Score 0.5 = mitad de los ingredientes.
        Score 0.0 = ningún ingrediente.
        """
        if not self.ingredients or not shopping_items:
            return 0.0

        shopping_normalized = [item.lower() for item in shopping_items]
        matches = 0

        for ingredient in self.ingredients:
            for item in shopping_normalized:
                if ingredient.name in item or item in ingredient.name:
                    matches += 1
                    break

        return matches / len(self.ingredients)


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPERS POR FUENTE
# ══════════════════════════════════════════════════════════════════════════════

class RecipeScraper:
    """Clase base para scrapers de recetas"""

    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

    async def fetch_page(self, url: str) -> Optional[str]:
        """Descarga una página HTML"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                return resp.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def scrape_recipes(self) -> list[Recipe]:
        """Método abstracto a implementar por subclases"""
        raise NotImplementedError


class RecetasDeRechupeteScraper(RecipeScraper):
    """Scraper para RecetasDeRechupete.com"""

    async def scrape_recipes(self) -> list[Recipe]:
        recipes = []

        for category_path in ["recetas/platos-principales/", "recetas/postres/", "recetas/verduras-y-legumbres/"]:
            url = f"{self.base_url}/{category_path}?paged=1"
            html = await self.fetch_page(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            recipe_links = soup.find_all("a", {"class": "recipe-link"})

            for link in recipe_links[:5]:  # Limitar a 5 por categoría para demo
                recipe_url = link.get("href", "")
                if not recipe_url:
                    continue

                recipe_html = await self.fetch_page(recipe_url)
                if not recipe_html:
                    continue

                recipe_soup = BeautifulSoup(recipe_html, "html.parser")

                try:
                    title = recipe_soup.find("h1")
                    if not title:
                        continue
                    title = title.get_text(strip=True)

                    # Ingredientes
                    ingredients = []
                    ing_section = recipe_soup.find("div", {"class": "ingredients"})
                    if ing_section:
                        for ing_item in ing_section.find_all("li"):
                            text = ing_item.get_text(strip=True)
                            if text:
                                # Parse simple: "200g de harina" → Ingredient("harina", "200", "g")
                                parts = text.split()
                                ing_name = " ".join(parts[2:]) if len(parts) > 2 else text
                                ing_qty = parts[0] if parts else None
                                ingredients.append(Ingredient(ing_name, ing_qty))

                    # Tiempo de preparación
                    time_text = recipe_soup.find("span", {"class": "prep-time"})
                    time_minutes = None
                    if time_text:
                        try:
                            time_minutes = int(time_text.get_text(strip=True).split()[0])
                        except:
                            pass

                    # Dificultad
                    difficulty = "media"
                    diff_text = recipe_soup.find("span", {"class": "difficulty"})
                    if diff_text:
                        difficulty = diff_text.get_text(strip=True).lower()

                    # Descripción
                    description = ""
                    desc_tag = recipe_soup.find("div", {"class": "description"})
                    if desc_tag:
                        description = desc_tag.get_text(strip=True)[:200]

                    # Imagen
                    image_url = ""
                    img_tag = recipe_soup.find("img", {"class": "recipe-image"})
                    if img_tag:
                        image_url = img_tag.get("src", "")

                    recipe = Recipe(
                        title=title,
                        source=self.source_name,
                        url=recipe_url,
                        ingredients=ingredients,
                        time_minutes=time_minutes,
                        difficulty=difficulty,
                        category=category_path.split("/")[1],
                        description=description,
                        image_url=image_url,
                    )
                    recipes.append(recipe)
                    logger.info(f"Scraped: {title}")

                except Exception as e:
                    logger.error(f"Error parsing recipe {recipe_url}: {e}")
                    continue

                await asyncio.sleep(1)  # Respetuoso con los servidores

        return recipes


class DirectoAlPaladarScraper(RecipeScraper):
    """Scraper para DirectoAlPaladar.com"""

    async def scrape_recipes(self) -> list[Recipe]:
        # Similar a RecetasDeRechupete pero con selectores diferentes
        recipes = []

        for category in ["platos-principales", "postres", "verduras"]:
            url = f"{self.base_url}/recetas/{category}/"
            html = await self.fetch_page(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            recipe_items = soup.find_all("article", {"class": "post"})

            for item in recipe_items[:3]:
                try:
                    title_tag = item.find("h2")
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)

                    link_tag = item.find("a")
                    recipe_url = link_tag.get("href", "") if link_tag else ""
                    if not recipe_url:
                        continue

                    # Fetch receta completa
                    recipe_html = await self.fetch_page(recipe_url)
                    if not recipe_html:
                        continue

                    recipe_soup = BeautifulSoup(recipe_html, "html.parser")

                    # Ingredientes
                    ingredients = []
                    for ing_text in recipe_soup.find_all("li", {"class": "ingredient"}):
                        text = ing_text.get_text(strip=True)
                        if text:
                            ingredients.append(Ingredient(text))

                    recipe = Recipe(
                        title=title,
                        source=self.source_name,
                        url=recipe_url,
                        ingredients=ingredients,
                        category=category,
                    )
                    recipes.append(recipe)
                    logger.info(f"Scraped: {title}")

                except Exception as e:
                    logger.error(f"Error parsing {recipe_url}: {e}")
                    continue

                await asyncio.sleep(1)

        return recipes


# ══════════════════════════════════════════════════════════════════════════════
# MAIN: EJECUTAR SCRAPERS Y GENERAR BD
# ══════════════════════════════════════════════════════════════════════════════

async def scrape_all_recipes() -> list[Recipe]:
    """Ejecuta todos los scrapers y combina resultados"""
    all_recipes = []

    scrapers = [
        RecetasDeRechupeteScraper("recetasderechupete", "https://www.recetasderechupete.com"),
        DirectoAlPaladarScraper("directo_al_paladar", "https://www.directoalpaladar.com"),
    ]

    for scraper in scrapers:
        logger.info(f"Starting scraper: {scraper.source_name}")
        try:
            recipes = await scraper.scrape_recipes()
            all_recipes.extend(recipes)
            logger.info(f"Scraped {len(recipes)} recipes from {scraper.source_name}")
        except Exception as e:
            logger.error(f"Scraper error {scraper.source_name}: {e}")

    return all_recipes


def save_recipes_json(recipes: list[Recipe], filepath: str = "recipes_database.json"):
    """Guarda las recetas en JSON para cargar en la BD"""
    data = {
        "total": len(recipes),
        "recipes": [r.to_dict() for r in recipes],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(recipes)} recipes to {filepath}")


# ══════════════════════════════════════════════════════════════════════════════
# RECETAS HARDCODEADAS PARA LA DEMO (mientras el scraper está en desarrollo)
# ══════════════════════════════════════════════════════════════════════════════

DEMO_RECIPES = [
    Recipe(
        title="Espaguetis a la carbonara",
        source="recetasderechupete",
        url="https://www.recetasderechupete.com/espaguetis-a-la-carbonara/",
        ingredients=[
            Ingredient("espaguetis", "400", "g"),
            Ingredient("huevos", "4", "ud"),
            Ingredient("bacon", "200", "g"),
            Ingredient("queso parmesano", "100", "g"),
            Ingredient("sal", "1", "pizca"),
            Ingredient("pimienta", "1", "pizca"),
        ],
        time_minutes=20,
        difficulty="fácil",
        category="platos-principales",
        description="Pasta italiana clásica cremosa y deliciosa",
        image_url="https://via.placeholder.com/300x200?text=Carbonara",
    ),
    Recipe(
        title="Salmón a la mantequilla",
        source="directo_al_paladar",
        url="https://www.directoalpaladar.com/salmon-mantequilla/",
        ingredients=[
            Ingredient("salmón fresco", "800", "g"),
            Ingredient("mantequilla", "100", "g"),
            Ingredient("limón", "2", "ud"),
            Ingredient("ajo", "3", "dientes"),
            Ingredient("perejil", "1", "manojo"),
            Ingredient("sal", "1", "pizca"),
        ],
        time_minutes=25,
        difficulty="fácil",
        category="pescados",
        description="Salmón tierno y jugoso con salsa de mantequilla",
        image_url="https://via.placeholder.com/300x200?text=Salmon",
    ),
    Recipe(
        title="Pollo al curry",
        source="recetasderechupete",
        url="https://www.recetasderechupete.com/pollo-curry/",
        ingredients=[
            Ingredient("pechuga de pollo", "800", "g"),
            Ingredient("curry en polvo", "3", "cucharadas"),
            Ingredient("leche de coco", "400", "ml"),
            Ingredient("cebolla", "2", "ud"),
            Ingredient("ajo", "4", "dientes"),
            Ingredient("jengibre fresco", "30", "g"),
            Ingredient("aceite de oliva", "3", "cucharadas"),
            Ingredient("sal", "1", "pizca"),
        ],
        time_minutes=40,
        difficulty="media",
        category="carnes",
        description="Curry cremoso con pollo tierno",
        image_url="https://via.placeholder.com/300x200?text=Curry",
    ),
    Recipe(
        title="Espinacas salteadas",
        source="directo_al_paladar",
        url="https://www.directoalpaladar.com/espinacas-salteadas/",
        ingredients=[
            Ingredient("espinacas frescas", "600", "g"),
            Ingredient("ajo", "4", "dientes"),
            Ingredient("aceite de oliva", "4", "cucharadas"),
            Ingredient("piñones", "50", "g"),
            Ingredient("sal", "1", "pizca"),
            Ingredient("pimienta", "1", "pizca"),
        ],
        time_minutes=10,
        difficulty="fácil",
        category="verduras",
        description="Verdura saludable y rápida",
        image_url="https://via.placeholder.com/300x200?text=Espinacas",
    ),
    Recipe(
        title="Tarta de chocolate",
        source="recetasderechupete",
        url="https://www.recetasderechupete.com/tarta-chocolate/",
        ingredients=[
            Ingredient("chocolate negro", "300", "g"),
            Ingredient("mantequilla", "200", "g"),
            Ingredient("huevos", "6", "ud"),
            Ingredient("azúcar", "200", "g"),
            Ingredient("harina", "100", "g"),
            Ingredient("sal", "1", "pizca"),
        ],
        time_minutes=45,
        difficulty="media",
        category="postres",
        description="Tarta decadente y fácil de hacer",
        image_url="https://via.placeholder.com/300x200?text=Chocolate",
    ),
    Recipe(
        title="Gazpacho andaluz",
        source="directo_al_paladar",
        url="https://www.directoalpaladar.com/gazpacho/",
        ingredients=[
            Ingredient("tomate", "1000", "g"),
            Ingredient("pepino", "1", "ud"),
            Ingredient("pimiento rojo", "1", "ud"),
            Ingredient("ajo", "2", "dientes"),
            Ingredient("pan", "100", "g"),
            Ingredient("aceite de oliva", "100", "ml"),
            Ingredient("vinagre", "2", "cucharadas"),
            Ingredient("sal", "1", "cucharadita"),
        ],
        time_minutes=15,
        difficulty="fácil",
        category="platos-principales",
        description="Sopa fría refrescante perfecta para verano",
        image_url="https://via.placeholder.com/300x200?text=Gazpacho",
    ),
]


def get_demo_recipes() -> list[Recipe]:
    """Retorna las recetas de demostración"""
    return DEMO_RECIPES


if __name__ == "__main__":
    # Para ejecutar manualmente:
    # python scrapers/recipes_scraper.py
    logging.basicConfig(level=logging.INFO)
    recipes = asyncio.run(scrape_all_recipes())
    if recipes:
        save_recipes_json(recipes)
    else:
        logger.warning("No recipes scraped, using demo recipes")
        save_recipes_json(get_demo_recipes())
