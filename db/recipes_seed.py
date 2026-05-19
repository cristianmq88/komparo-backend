"""
Catálogo inicial de recetas. Se siembra en BD al arrancar si la tabla está vacía.

Cada receta es un dict con la misma forma que el modelo `Recipe`.
"""

DIFFICULTY_EASY = "fácil"
DIFFICULTY_MED = "media"
DIFFICULTY_HARD = "difícil"

CAT_MAIN = "platos-principales"
CAT_FISH = "pescados"
CAT_MEAT = "carnes"
CAT_PASTA = "pasta-y-arroces"
CAT_SOUP = "sopas-y-cremas"
CAT_SALAD = "ensaladas"
CAT_DESSERT = "postres"
CAT_VEG = "vegetariano"
CAT_BREAKFAST = "desayunos-meriendas"
CAT_APERITIVO = "aperitivos"
CAT_INTL = "internacional"


def _i(name, q, u):
    return {"name": name, "quantity": str(q), "unit": u}


RECIPES = [
    # ── Platos principales clásicos españoles ────────────────────────────
    {
        "id": "recipe_1", "title": "Tortilla de patatas",
        "description": "El clásico de la cocina española",
        "servings": 6, "time_minutes": 35,
        "difficulty": DIFFICULTY_MED, "category": CAT_MAIN,
        "ingredients": [
            _i("patatas", 1, "kg"), _i("huevos", 6, "ud"),
            _i("cebolla", 1, "ud"), _i("aceite oliva", 200, "ml"),
            _i("sal", 1, "cucharadita"),
        ],
    },
    {
        "id": "recipe_2", "title": "Gazpacho andaluz",
        "description": "Sopa fría refrescante de verano",
        "servings": 4, "time_minutes": 15,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SOUP,
        "ingredients": [
            _i("tomate", 1000, "g"), _i("pepino", 1, "ud"),
            _i("pimiento rojo", 1, "ud"), _i("ajo", 2, "dientes"),
            _i("aceite oliva", 80, "ml"), _i("vinagre", 30, "ml"),
            _i("pan", 1, "rebanada"),
        ],
    },
    {
        "id": "recipe_3", "title": "Paella valenciana",
        "description": "Arroz tradicional con pollo y conejo",
        "servings": 6, "time_minutes": 60,
        "difficulty": DIFFICULTY_HARD, "category": CAT_PASTA,
        "ingredients": [
            _i("arroz bomba", 500, "g"), _i("pollo", 500, "g"),
            _i("conejo", 500, "g"), _i("judía verde", 200, "g"),
            _i("garrofón", 150, "g"), _i("tomate", 1, "ud"),
            _i("pimentón", 1, "cucharada"), _i("azafrán", 1, "pizca"),
            _i("aceite oliva", 100, "ml"),
        ],
    },
    {
        "id": "recipe_4", "title": "Cocido madrileño",
        "description": "Cocido de garbanzos, carnes y verduras",
        "servings": 6, "time_minutes": 180,
        "difficulty": DIFFICULTY_MED, "category": CAT_MAIN,
        "ingredients": [
            _i("garbanzos", 500, "g"), _i("morcillo de ternera", 400, "g"),
            _i("pollo", 300, "g"), _i("tocino", 200, "g"),
            _i("chorizo", 200, "g"), _i("morcilla", 200, "g"),
            _i("zanahoria", 3, "ud"), _i("patata", 4, "ud"),
            _i("repollo", 1, "ud"), _i("fideos", 100, "g"),
        ],
    },
    {
        "id": "recipe_5", "title": "Lentejas con chorizo",
        "description": "Guiso reconfortante de toda la vida",
        "servings": 4, "time_minutes": 60,
        "difficulty": DIFFICULTY_EASY, "category": CAT_MAIN,
        "ingredients": [
            _i("lentejas", 400, "g"), _i("chorizo", 200, "g"),
            _i("zanahoria", 2, "ud"), _i("cebolla", 1, "ud"),
            _i("ajo", 2, "dientes"), _i("pimentón", 1, "cucharadita"),
            _i("aceite oliva", 50, "ml"), _i("laurel", 1, "hoja"),
        ],
    },
    {
        "id": "recipe_6", "title": "Albóndigas en salsa de tomate",
        "description": "Albóndigas tiernas con salsa casera",
        "servings": 4, "time_minutes": 50,
        "difficulty": DIFFICULTY_EASY, "category": CAT_MEAT,
        "ingredients": [
            _i("carne picada", 600, "g"), _i("huevo", 1, "ud"),
            _i("pan rallado", 80, "g"), _i("ajo", 2, "dientes"),
            _i("tomate triturado", 500, "g"), _i("cebolla", 1, "ud"),
            _i("perejil", 1, "manojo"),
        ],
    },
    {
        "id": "recipe_7", "title": "Pisto manchego",
        "description": "Verduras de la huerta sofritas",
        "servings": 4, "time_minutes": 45,
        "difficulty": DIFFICULTY_EASY, "category": CAT_VEG,
        "ingredients": [
            _i("calabacín", 2, "ud"), _i("berenjena", 1, "ud"),
            _i("pimiento verde", 1, "ud"), _i("pimiento rojo", 1, "ud"),
            _i("cebolla", 1, "ud"), _i("tomate triturado", 400, "g"),
            _i("aceite oliva", 60, "ml"),
        ],
    },
    {
        "id": "recipe_8", "title": "Pollo al ajillo",
        "description": "Pollo dorado con ajo y vino blanco",
        "servings": 4, "time_minutes": 40,
        "difficulty": DIFFICULTY_EASY, "category": CAT_MEAT,
        "ingredients": [
            _i("pollo troceado", 1200, "g"), _i("ajo", 8, "dientes"),
            _i("vino blanco", 150, "ml"), _i("aceite oliva", 80, "ml"),
            _i("laurel", 2, "hojas"), _i("perejil", 1, "manojo"),
        ],
    },
    {
        "id": "recipe_9", "title": "Solomillo al whisky",
        "description": "Solomillo de cerdo con salsa especiada",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_MED, "category": CAT_MEAT,
        "ingredients": [
            _i("solomillo de cerdo", 800, "g"), _i("ajo", 6, "dientes"),
            _i("whisky", 100, "ml"), _i("limón", 1, "ud"),
            _i("caldo de carne", 200, "ml"), _i("aceite oliva", 50, "ml"),
        ],
    },
    {
        "id": "recipe_10", "title": "Conejo al ajillo",
        "description": "Conejo tierno con ajo y romero",
        "servings": 4, "time_minutes": 50,
        "difficulty": DIFFICULTY_MED, "category": CAT_MEAT,
        "ingredients": [
            _i("conejo", 1, "ud"), _i("ajo", 10, "dientes"),
            _i("vino blanco", 200, "ml"), _i("romero", 1, "ramita"),
            _i("aceite oliva", 80, "ml"),
        ],
    },

    # ── Pasta y arroces ──────────────────────────────────────────────────
    {
        "id": "recipe_11", "title": "Espaguetis a la carbonara",
        "description": "Pasta italiana cremosa con bacon",
        "servings": 4, "time_minutes": 20,
        "difficulty": DIFFICULTY_EASY, "category": CAT_PASTA,
        "ingredients": [
            _i("espaguetis", 400, "g"), _i("huevos", 4, "ud"),
            _i("bacon", 200, "g"), _i("queso parmesano", 100, "g"),
            _i("pimienta negra", 1, "cucharadita"),
        ],
    },
    {
        "id": "recipe_12", "title": "Macarrones con tomate",
        "description": "Plato rápido para toda la familia",
        "servings": 4, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_PASTA,
        "ingredients": [
            _i("macarrones", 400, "g"), _i("tomate triturado", 500, "g"),
            _i("cebolla", 1, "ud"), _i("ajo", 2, "dientes"),
            _i("queso rallado", 80, "g"), _i("aceite oliva", 40, "ml"),
        ],
    },
    {
        "id": "recipe_13", "title": "Lasaña de carne",
        "description": "Lasaña casera al horno con bechamel",
        "servings": 6, "time_minutes": 75,
        "difficulty": DIFFICULTY_MED, "category": CAT_PASTA,
        "ingredients": [
            _i("placas de lasaña", 12, "ud"), _i("carne picada", 600, "g"),
            _i("tomate triturado", 500, "g"), _i("cebolla", 1, "ud"),
            _i("leche", 600, "ml"), _i("mantequilla", 60, "g"),
            _i("harina", 60, "g"), _i("queso rallado", 150, "g"),
        ],
    },
    {
        "id": "recipe_14", "title": "Pasta al pesto",
        "description": "Pasta con salsa de albahaca y piñones",
        "servings": 4, "time_minutes": 20,
        "difficulty": DIFFICULTY_EASY, "category": CAT_PASTA,
        "ingredients": [
            _i("pasta", 400, "g"), _i("albahaca fresca", 50, "g"),
            _i("piñones", 50, "g"), _i("queso parmesano", 80, "g"),
            _i("ajo", 1, "diente"), _i("aceite oliva", 100, "ml"),
        ],
    },
    {
        "id": "recipe_15", "title": "Arroz con pollo",
        "description": "Arroz caldoso tradicional",
        "servings": 4, "time_minutes": 45,
        "difficulty": DIFFICULTY_EASY, "category": CAT_PASTA,
        "ingredients": [
            _i("arroz", 400, "g"), _i("pollo troceado", 600, "g"),
            _i("pimiento rojo", 1, "ud"), _i("cebolla", 1, "ud"),
            _i("tomate", 2, "ud"), _i("ajo", 2, "dientes"),
            _i("caldo de pollo", 1, "l"), _i("azafrán", 1, "pizca"),
        ],
    },
    {
        "id": "recipe_16", "title": "Risotto de setas",
        "description": "Arroz cremoso italiano con setas",
        "servings": 4, "time_minutes": 35,
        "difficulty": DIFFICULTY_MED, "category": CAT_VEG,
        "ingredients": [
            _i("arroz arborio", 320, "g"), _i("setas variadas", 300, "g"),
            _i("cebolla", 1, "ud"), _i("vino blanco", 100, "ml"),
            _i("caldo de verduras", 1, "l"), _i("queso parmesano", 80, "g"),
            _i("mantequilla", 40, "g"),
        ],
    },
    {
        "id": "recipe_17", "title": "Espaguetis a la boloñesa",
        "description": "Pasta con salsa de carne italiana",
        "servings": 4, "time_minutes": 50,
        "difficulty": DIFFICULTY_EASY, "category": CAT_PASTA,
        "ingredients": [
            _i("espaguetis", 400, "g"), _i("carne picada", 400, "g"),
            _i("tomate triturado", 500, "g"), _i("cebolla", 1, "ud"),
            _i("zanahoria", 1, "ud"), _i("ajo", 2, "dientes"),
            _i("vino tinto", 100, "ml"),
        ],
    },
    {
        "id": "recipe_18", "title": "Arroz tres delicias",
        "description": "Arroz frito estilo oriental",
        "servings": 4, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_INTL,
        "ingredients": [
            _i("arroz", 400, "g"), _i("huevos", 3, "ud"),
            _i("guisantes", 150, "g"), _i("zanahoria", 1, "ud"),
            _i("jamón cocido", 150, "g"), _i("salsa de soja", 30, "ml"),
        ],
    },

    # ── Pescados ─────────────────────────────────────────────────────────
    {
        "id": "recipe_19", "title": "Salmón a la mantequilla",
        "description": "Salmón tierno y jugoso al sartén",
        "servings": 4, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_FISH,
        "ingredients": [
            _i("salmón fresco", 800, "g"), _i("mantequilla", 100, "g"),
            _i("limón", 2, "ud"), _i("eneldo", 1, "cucharada"),
        ],
    },
    {
        "id": "recipe_20", "title": "Merluza a la romana",
        "description": "Merluza rebozada y frita",
        "servings": 4, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_FISH,
        "ingredients": [
            _i("merluza", 800, "g"), _i("huevos", 2, "ud"),
            _i("harina", 100, "g"), _i("aceite oliva", 300, "ml"),
            _i("limón", 1, "ud"),
        ],
    },
    {
        "id": "recipe_21", "title": "Bacalao al pil-pil",
        "description": "Clásico vasco con emulsión de aceite",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_HARD, "category": CAT_FISH,
        "ingredients": [
            _i("bacalao desalado", 800, "g"), _i("ajo", 6, "dientes"),
            _i("guindilla", 2, "ud"), _i("aceite oliva", 250, "ml"),
        ],
    },
    {
        "id": "recipe_22", "title": "Mejillones al vapor",
        "description": "Mejillones con limón y laurel",
        "servings": 4, "time_minutes": 15,
        "difficulty": DIFFICULTY_EASY, "category": CAT_FISH,
        "ingredients": [
            _i("mejillones", 2, "kg"), _i("limón", 1, "ud"),
            _i("laurel", 2, "hojas"), _i("vino blanco", 100, "ml"),
        ],
    },
    {
        "id": "recipe_23", "title": "Sardinas a la plancha",
        "description": "Sardinas frescas con ajo y perejil",
        "servings": 4, "time_minutes": 20,
        "difficulty": DIFFICULTY_EASY, "category": CAT_FISH,
        "ingredients": [
            _i("sardinas", 1, "kg"), _i("ajo", 3, "dientes"),
            _i("perejil", 1, "manojo"), _i("aceite oliva", 50, "ml"),
            _i("sal gruesa", 1, "cucharada"),
        ],
    },
    {
        "id": "recipe_24", "title": "Calamares en su tinta",
        "description": "Guiso oscuro con arroz blanco",
        "servings": 4, "time_minutes": 60,
        "difficulty": DIFFICULTY_MED, "category": CAT_FISH,
        "ingredients": [
            _i("calamares", 1, "kg"), _i("tinta de calamar", 4, "sobres"),
            _i("cebolla", 2, "ud"), _i("tomate", 2, "ud"),
            _i("ajo", 2, "dientes"), _i("vino blanco", 100, "ml"),
        ],
    },
    {
        "id": "recipe_25", "title": "Dorada al horno",
        "description": "Dorada con patatas panadera",
        "servings": 4, "time_minutes": 50,
        "difficulty": DIFFICULTY_EASY, "category": CAT_FISH,
        "ingredients": [
            _i("dorada", 2, "ud"), _i("patata", 4, "ud"),
            _i("cebolla", 1, "ud"), _i("limón", 1, "ud"),
            _i("aceite oliva", 80, "ml"), _i("vino blanco", 100, "ml"),
        ],
    },
    {
        "id": "recipe_26", "title": "Atún encebollado",
        "description": "Atún rojo con cebolla pochada",
        "servings": 4, "time_minutes": 35,
        "difficulty": DIFFICULTY_EASY, "category": CAT_FISH,
        "ingredients": [
            _i("atún fresco", 600, "g"), _i("cebolla", 3, "ud"),
            _i("vino blanco", 100, "ml"), _i("vinagre", 30, "ml"),
            _i("laurel", 2, "hojas"), _i("aceite oliva", 60, "ml"),
        ],
    },

    # ── Sopas y cremas ───────────────────────────────────────────────────
    {
        "id": "recipe_27", "title": "Crema de calabaza",
        "description": "Suave y reconfortante para el invierno",
        "servings": 4, "time_minutes": 35,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SOUP,
        "ingredients": [
            _i("calabaza", 1, "kg"), _i("patata", 2, "ud"),
            _i("cebolla", 1, "ud"), _i("caldo de verduras", 1, "l"),
            _i("nata", 100, "ml"),
        ],
    },
    {
        "id": "recipe_28", "title": "Crema de calabacín",
        "description": "Crema ligera con queso fundido",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SOUP,
        "ingredients": [
            _i("calabacín", 4, "ud"), _i("patata", 1, "ud"),
            _i("cebolla", 1, "ud"), _i("queso en porciones", 4, "ud"),
            _i("caldo de pollo", 800, "ml"),
        ],
    },
    {
        "id": "recipe_29", "title": "Sopa de ajo castellana",
        "description": "Sopa tradicional con pan y huevo",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SOUP,
        "ingredients": [
            _i("pan duro", 200, "g"), _i("ajo", 8, "dientes"),
            _i("huevos", 4, "ud"), _i("pimentón", 1, "cucharada"),
            _i("aceite oliva", 60, "ml"), _i("caldo de pollo", 1, "l"),
        ],
    },
    {
        "id": "recipe_30", "title": "Sopa de pollo",
        "description": "Reconfortante con fideos y verduras",
        "servings": 4, "time_minutes": 60,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SOUP,
        "ingredients": [
            _i("pollo", 500, "g"), _i("zanahoria", 2, "ud"),
            _i("puerro", 1, "ud"), _i("apio", 1, "rama"),
            _i("fideos", 100, "g"),
        ],
    },
    {
        "id": "recipe_31", "title": "Sopa de pescado",
        "description": "Sopa marinera con rebanadas de pan",
        "servings": 4, "time_minutes": 45,
        "difficulty": DIFFICULTY_MED, "category": CAT_SOUP,
        "ingredients": [
            _i("rape", 400, "g"), _i("merluza", 300, "g"),
            _i("gambas", 200, "g"), _i("cebolla", 1, "ud"),
            _i("tomate", 2, "ud"), _i("pan", 4, "rebanadas"),
        ],
    },
    {
        "id": "recipe_32", "title": "Salmorejo cordobés",
        "description": "Crema fría densa con jamón y huevo",
        "servings": 4, "time_minutes": 15,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SOUP,
        "ingredients": [
            _i("tomate maduro", 1, "kg"), _i("pan", 200, "g"),
            _i("ajo", 1, "diente"), _i("aceite oliva", 150, "ml"),
            _i("jamón serrano", 100, "g"), _i("huevos", 2, "ud"),
        ],
    },

    # ── Ensaladas ────────────────────────────────────────────────────────
    {
        "id": "recipe_33", "title": "Ensalada césar",
        "description": "Lechuga, pollo y aliño cremoso",
        "servings": 4, "time_minutes": 20,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SALAD,
        "ingredients": [
            _i("lechuga romana", 1, "ud"), _i("pechuga de pollo", 400, "g"),
            _i("queso parmesano", 60, "g"), _i("pan", 4, "rebanadas"),
            _i("mayonesa", 80, "g"), _i("ajo", 1, "diente"),
            _i("limón", 1, "ud"),
        ],
    },
    {
        "id": "recipe_34", "title": "Ensaladilla rusa",
        "description": "Patata, atún y mayonesa",
        "servings": 6, "time_minutes": 40,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SALAD,
        "ingredients": [
            _i("patata", 4, "ud"), _i("zanahoria", 2, "ud"),
            _i("guisantes", 150, "g"), _i("huevos", 3, "ud"),
            _i("atún en conserva", 200, "g"), _i("mayonesa", 200, "g"),
            _i("aceitunas", 50, "g"),
        ],
    },
    {
        "id": "recipe_35", "title": "Ensalada caprese",
        "description": "Tomate, mozzarella y albahaca",
        "servings": 4, "time_minutes": 10,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SALAD,
        "ingredients": [
            _i("tomate", 4, "ud"), _i("mozzarella fresca", 250, "g"),
            _i("albahaca fresca", 1, "manojo"), _i("aceite oliva", 50, "ml"),
            _i("vinagre balsámico", 20, "ml"),
        ],
    },
    {
        "id": "recipe_36", "title": "Ensalada de pasta",
        "description": "Pasta fría con atún y verduras",
        "servings": 4, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_SALAD,
        "ingredients": [
            _i("pasta corta", 300, "g"), _i("atún en conserva", 150, "g"),
            _i("tomate cherry", 200, "g"), _i("aceitunas", 80, "g"),
            _i("maíz", 100, "g"), _i("queso fresco", 100, "g"),
        ],
    },

    # ── Aperitivos y entrantes ───────────────────────────────────────────
    {
        "id": "recipe_37", "title": "Croquetas de jamón",
        "description": "Croquetas caseras crujientes",
        "servings": 6, "time_minutes": 90,
        "difficulty": DIFFICULTY_MED, "category": CAT_APERITIVO,
        "ingredients": [
            _i("jamón serrano", 200, "g"), _i("leche", 800, "ml"),
            _i("harina", 120, "g"), _i("mantequilla", 80, "g"),
            _i("pan rallado", 200, "g"), _i("huevos", 2, "ud"),
        ],
    },
    {
        "id": "recipe_38", "title": "Hummus casero",
        "description": "Crema de garbanzos con tahini",
        "servings": 4, "time_minutes": 10,
        "difficulty": DIFFICULTY_EASY, "category": CAT_APERITIVO,
        "ingredients": [
            _i("garbanzos cocidos", 400, "g"), _i("tahini", 40, "g"),
            _i("limón", 1, "ud"), _i("ajo", 1, "diente"),
            _i("aceite oliva", 50, "ml"), _i("comino", 1, "cucharadita"),
        ],
    },
    {
        "id": "recipe_39", "title": "Empanadillas de atún",
        "description": "Pequeñas empanadillas al horno",
        "servings": 4, "time_minutes": 35,
        "difficulty": DIFFICULTY_EASY, "category": CAT_APERITIVO,
        "ingredients": [
            _i("obleas para empanadillas", 16, "ud"),
            _i("atún en conserva", 200, "g"),
            _i("tomate frito", 150, "g"), _i("huevo", 1, "ud"),
            _i("cebolla", 1, "ud"),
        ],
    },
    {
        "id": "recipe_40", "title": "Tortilla francesa rellena",
        "description": "Tortilla con queso y jamón",
        "servings": 2, "time_minutes": 10,
        "difficulty": DIFFICULTY_EASY, "category": CAT_APERITIVO,
        "ingredients": [
            _i("huevos", 4, "ud"), _i("queso", 80, "g"),
            _i("jamón cocido", 80, "g"), _i("aceite oliva", 20, "ml"),
        ],
    },

    # ── Vegetariano ──────────────────────────────────────────────────────
    {
        "id": "recipe_41", "title": "Pimientos rellenos",
        "description": "Pimientos asados rellenos de arroz",
        "servings": 4, "time_minutes": 60,
        "difficulty": DIFFICULTY_MED, "category": CAT_VEG,
        "ingredients": [
            _i("pimientos rojos", 4, "ud"), _i("arroz", 200, "g"),
            _i("cebolla", 1, "ud"), _i("tomate", 2, "ud"),
            _i("queso rallado", 100, "g"),
        ],
    },
    {
        "id": "recipe_42", "title": "Curry de garbanzos",
        "description": "Garbanzos con leche de coco y especias",
        "servings": 4, "time_minutes": 35,
        "difficulty": DIFFICULTY_EASY, "category": CAT_VEG,
        "ingredients": [
            _i("garbanzos cocidos", 500, "g"), _i("leche de coco", 400, "ml"),
            _i("tomate triturado", 200, "g"), _i("cebolla", 1, "ud"),
            _i("curry en polvo", 2, "cucharadas"), _i("ajo", 2, "dientes"),
            _i("jengibre", 1, "trozo"),
        ],
    },

    # ── Internacional ────────────────────────────────────────────────────
    {
        "id": "recipe_43", "title": "Pollo al curry",
        "description": "Pollo cremoso con curry y leche de coco",
        "servings": 4, "time_minutes": 40,
        "difficulty": DIFFICULTY_MED, "category": CAT_INTL,
        "ingredients": [
            _i("pechuga de pollo", 800, "g"), _i("curry en polvo", 3, "cucharadas"),
            _i("leche de coco", 400, "ml"), _i("cebolla", 2, "ud"),
            _i("ajo", 2, "dientes"), _i("jengibre", 1, "trozo"),
            _i("arroz basmati", 300, "g"),
        ],
    },
    {
        "id": "recipe_44", "title": "Tacos de pollo",
        "description": "Tortillas con pollo y guacamole",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_EASY, "category": CAT_INTL,
        "ingredients": [
            _i("tortillas de maíz", 12, "ud"), _i("pechuga de pollo", 600, "g"),
            _i("aguacate", 2, "ud"), _i("tomate", 2, "ud"),
            _i("cebolla morada", 1, "ud"), _i("lima", 2, "ud"),
            _i("cilantro", 1, "manojo"),
        ],
    },
    {
        "id": "recipe_45", "title": "Pad thai",
        "description": "Fideos salteados estilo tailandés",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_MED, "category": CAT_INTL,
        "ingredients": [
            _i("fideos de arroz", 250, "g"), _i("gambas", 200, "g"),
            _i("huevos", 2, "ud"), _i("brotes de soja", 150, "g"),
            _i("cacahuetes", 60, "g"), _i("salsa de soja", 40, "ml"),
            _i("lima", 1, "ud"),
        ],
    },
    {
        "id": "recipe_46", "title": "Hamburguesa casera",
        "description": "Burger con queso y pan brioche",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_EASY, "category": CAT_INTL,
        "ingredients": [
            _i("carne picada", 600, "g"), _i("pan de hamburguesa", 4, "ud"),
            _i("queso cheddar", 4, "lonchas"), _i("tomate", 1, "ud"),
            _i("lechuga", 4, "hojas"), _i("cebolla morada", 1, "ud"),
        ],
    },

    # ── Postres ──────────────────────────────────────────────────────────
    {
        "id": "recipe_47", "title": "Tarta de chocolate",
        "description": "Tarta densa de chocolate negro",
        "servings": 8, "time_minutes": 60,
        "difficulty": DIFFICULTY_MED, "category": CAT_DESSERT,
        "ingredients": [
            _i("chocolate negro", 300, "g"), _i("mantequilla", 200, "g"),
            _i("huevos", 6, "ud"), _i("azúcar", 200, "g"),
            _i("harina", 100, "g"),
        ],
    },
    {
        "id": "recipe_48", "title": "Flan de huevo",
        "description": "Flan casero con caramelo líquido",
        "servings": 6, "time_minutes": 60,
        "difficulty": DIFFICULTY_MED, "category": CAT_DESSERT,
        "ingredients": [
            _i("huevos", 6, "ud"), _i("leche", 750, "ml"),
            _i("azúcar", 200, "g"), _i("vainilla", 1, "cucharadita"),
        ],
    },
    {
        "id": "recipe_49", "title": "Arroz con leche",
        "description": "Postre cremoso con canela",
        "servings": 6, "time_minutes": 50,
        "difficulty": DIFFICULTY_EASY, "category": CAT_DESSERT,
        "ingredients": [
            _i("arroz", 200, "g"), _i("leche", 1, "l"),
            _i("azúcar", 150, "g"), _i("canela en rama", 1, "ud"),
            _i("limón", 1, "ud"),
        ],
    },
    {
        "id": "recipe_50", "title": "Natillas caseras",
        "description": "Natillas suaves con galleta",
        "servings": 6, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_DESSERT,
        "ingredients": [
            _i("leche", 1, "l"), _i("huevos", 4, "ud"),
            _i("azúcar", 150, "g"), _i("maicena", 30, "g"),
            _i("canela", 1, "cucharadita"), _i("galletas", 6, "ud"),
        ],
    },
    {
        "id": "recipe_51", "title": "Brownie de chocolate",
        "description": "Bizcocho denso con nueces",
        "servings": 8, "time_minutes": 45,
        "difficulty": DIFFICULTY_EASY, "category": CAT_DESSERT,
        "ingredients": [
            _i("chocolate negro", 200, "g"), _i("mantequilla", 200, "g"),
            _i("huevos", 4, "ud"), _i("azúcar", 250, "g"),
            _i("harina", 120, "g"), _i("nueces", 100, "g"),
        ],
    },
    {
        "id": "recipe_52", "title": "Tiramisú",
        "description": "Postre italiano con café y mascarpone",
        "servings": 6, "time_minutes": 30,
        "difficulty": DIFFICULTY_MED, "category": CAT_DESSERT,
        "ingredients": [
            _i("mascarpone", 500, "g"), _i("huevos", 4, "ud"),
            _i("azúcar", 120, "g"), _i("bizcochos de soletilla", 24, "ud"),
            _i("café", 300, "ml"), _i("cacao en polvo", 30, "g"),
        ],
    },
    {
        "id": "recipe_53", "title": "Cheesecake",
        "description": "Tarta de queso al horno con mermelada",
        "servings": 8, "time_minutes": 75,
        "difficulty": DIFFICULTY_MED, "category": CAT_DESSERT,
        "ingredients": [
            _i("queso crema", 600, "g"), _i("nata para montar", 300, "ml"),
            _i("huevos", 4, "ud"), _i("azúcar", 150, "g"),
            _i("galletas", 200, "g"), _i("mantequilla", 80, "g"),
            _i("mermelada", 200, "g"),
        ],
    },
    {
        "id": "recipe_54", "title": "Crema catalana",
        "description": "Crema con costra de azúcar quemada",
        "servings": 4, "time_minutes": 30,
        "difficulty": DIFFICULTY_MED, "category": CAT_DESSERT,
        "ingredients": [
            _i("leche", 500, "ml"), _i("yemas de huevo", 4, "ud"),
            _i("azúcar", 120, "g"), _i("maicena", 20, "g"),
            _i("canela", 1, "rama"), _i("limón", 1, "ud"),
        ],
    },

    # ── Desayunos y meriendas ────────────────────────────────────────────
    {
        "id": "recipe_55", "title": "Bizcocho de yogur",
        "description": "Bizcocho esponjoso para merendar",
        "servings": 8, "time_minutes": 50,
        "difficulty": DIFFICULTY_EASY, "category": CAT_BREAKFAST,
        "ingredients": [
            _i("yogur natural", 1, "ud"), _i("huevos", 3, "ud"),
            _i("azúcar", 200, "g"), _i("harina", 300, "g"),
            _i("aceite girasol", 150, "ml"), _i("levadura", 1, "sobre"),
            _i("limón", 1, "ud"),
        ],
    },
    {
        "id": "recipe_56", "title": "Tortitas americanas",
        "description": "Pancakes con sirope de arce",
        "servings": 4, "time_minutes": 25,
        "difficulty": DIFFICULTY_EASY, "category": CAT_BREAKFAST,
        "ingredients": [
            _i("harina", 200, "g"), _i("leche", 250, "ml"),
            _i("huevos", 2, "ud"), _i("azúcar", 40, "g"),
            _i("levadura", 1, "sobre"), _i("mantequilla", 30, "g"),
        ],
    },
    {
        "id": "recipe_57", "title": "Magdalenas caseras",
        "description": "Clásicas magdalenas de limón",
        "servings": 12, "time_minutes": 30,
        "difficulty": DIFFICULTY_EASY, "category": CAT_BREAKFAST,
        "ingredients": [
            _i("huevos", 3, "ud"), _i("azúcar", 180, "g"),
            _i("aceite girasol", 180, "ml"), _i("leche", 60, "ml"),
            _i("harina", 250, "g"), _i("levadura", 1, "sobre"),
            _i("limón", 1, "ud"),
        ],
    },
    {
        "id": "recipe_58", "title": "Granola casera",
        "description": "Mezcla de avena, frutos secos y miel",
        "servings": 10, "time_minutes": 35,
        "difficulty": DIFFICULTY_EASY, "category": CAT_BREAKFAST,
        "ingredients": [
            _i("copos de avena", 300, "g"), _i("nueces", 100, "g"),
            _i("almendras", 100, "g"), _i("miel", 100, "g"),
            _i("aceite girasol", 60, "ml"), _i("pasas", 80, "g"),
            _i("canela", 1, "cucharadita"),
        ],
    },
]


def get_recipe_by_id(recipe_id: str):
    for r in RECIPES:
        if r["id"] == recipe_id:
            return r
    return None
