"""
api/routes/recipes.py - Endpoints para recetas
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db import crud, schemas
from db.recipes_models import (
    get_recipes_by_ingredients, get_recipe_details, search_recipes,
    save_favorite_recipe, remove_favorite_recipe, get_user_favorites
)
from api.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/recipes", tags=["recipes"])

# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS PYDANTIC
# ══════════════════════════════════════════════════════════════════════════════

class IngredientSchema(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None


class RecipeOut(BaseModel):
    id: str
    title: str
    source: str
    url: str
    description: str
    image_url: str
    servings: int
    time_minutes: Optional[int]
    difficulty: str
    category: str
    ingredients: list[IngredientSchema]

    class Config:
        from_attributes = True


class RecipeWithMatchScore(BaseModel):
    recipe: RecipeOut
    match_score: float  # 0.0 a 1.0 — qué % de ingredientes tienes


class CreateListFromRecipe(BaseModel):
    recipe_id: str
    servings: int = 4  # Número de comensales (por si la receta es para 4 pero cocinas para 6)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/search", response_model=list[RecipeOut])
def search_recipes_endpoint(
    q: str = "",
    category: str = "",
    difficulty: str = "",
    max_time: int = 60,
    db: Session = Depends(get_db)
):
    """
    Busca recetas por término, categoría, dificultad y tiempo.
    
    Ejemplo: GET /recipes/search?q=pollo&difficulty=fácil&max_time=30
    """
    recipes = search_recipes(db, q, category, difficulty, max_time)
    return recipes


@router.get("/by-shopping-list/{list_id}", response_model=list[RecipeWithMatchScore])
def get_recipes_for_shopping_list(
    list_id: str,
    min_match: float = 0.3,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⭐ FLUJO 1: CESTA → RECETAS SUGERIDAS
    
    Dado una lista de la compra, retorna recetas que puedes hacer con esos ingredientes.
    Ordena por % de ingredientes que ya tienes.
    
    Ejemplo:
    - Cesta: leche, huevos, harina, azúcar, chocolate
    - Recetas sugeridas: "Tarta de chocolate" (100%), "Crepes" (80%), "Pudín" (60%)
    """
    # Obtener la cesta
    the_list = crud.get_list(db, list_id, current_user.id)
    if not the_list:
        raise HTTPException(404, "Lista no encontrada")
    
    # Extraer nombres de productos de la lista
    shopping_items = [
        item.canonical_name or item.custom_name 
        for item in the_list.items
    ]
    
    # Buscar recetas que coincidan
    matched_recipes = get_recipes_by_ingredients(db, shopping_items, min_match)
    
    # Convertir a schema
    result = [
        RecipeWithMatchScore(
            recipe=RecipeOut.from_orm(recipe),
            match_score=score
        )
        for recipe, score in matched_recipes
    ]
    
    return result


@router.post("/create-list-from-recipe/{recipe_id}", response_model=schemas.ShoppingListOut)
def create_shopping_list_from_recipe(
    recipe_id: str,
    data: CreateListFromRecipe,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⭐ FLUJO 2: RECETA → LISTA DE LA COMPRA
    
    Dada una receta, crea una nueva cesta con todos sus ingredientes.
    
    Ejemplo:
    - Receta: "Pollo al curry"
    - Se crea cesta "Pollo al curry" con: pechuga de pollo ×800g, curry ×3, leche de coco ×400ml...
    - El usuario puede luego:
      - Añadir más productos
      - Comparar en qué súper sale más barato
      - Compartir con otros
    """
    # Obtener detalles de la receta
    recipe = get_recipe_details(db, recipe_id)
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")
    
    # Crear una cesta con el nombre de la receta
    list_data = schemas.ShoppingListCreate(name=recipe.title)
    new_list = crud.create_shopping_list(db, current_user.id, list_data)
    
    # Añadir cada ingrediente como item de la cesta
    for ingredient in recipe.ingredients or []:
        ing_name = ingredient.get("name", "")
        quantity = ingredient.get("quantity", "")
        unit = ingredient.get("unit", "")
        
        # Construir nombre del producto: "400g harina" o "1L leche"
        full_name = f"{quantity} {unit} {ing_name}".strip()
        
        try:
            item_data = schemas.ListItemCreate(
                custom_name=full_name,
                quantity=float(quantity) if quantity and quantity.isdigit() else 1.0
            )
            crud.add_item_to_list(db, new_list.id, item_data)
        except Exception as e:
            # Si falla un ingrediente, continuar con los demás
            pass
    
    # Guardar el link receta ↔ lista
    from db.recipes_models import ListFromRecipe
    list_recipe = ListFromRecipe(
        list_id=new_list.id,
        recipe_id=recipe_id,
        servings_used=data.servings
    )
    db.add(list_recipe)
    db.commit()
    
    return schemas.ShoppingListOut.from_orm(new_list)


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(
    recipe_id: str,
    db: Session = Depends(get_db)
):
    """Obtiene los detalles de una receta específica"""
    recipe = get_recipe_details(db, recipe_id)
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")
    return recipe


@router.post("/{recipe_id}/favorite")
def favorite_recipe(
    recipe_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca una receta como favorita"""
    recipe = get_recipe_details(db, recipe_id)
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")
    
    success = save_favorite_recipe(db, current_user.id, recipe_id)
    return {"favorited": success}


@router.delete("/{recipe_id}/favorite")
def unfavorite_recipe(
    recipe_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Quita una receta de favoritos"""
    remove_favorite_recipe(db, current_user.id, recipe_id)
    return {"unfavorited": True}


@router.get("/favorites/my", response_model=list[RecipeOut])
def get_my_favorites(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todas las recetas favoritas del usuario"""
    recipes = get_user_favorites(db, current_user.id)
    return recipes


@router.get("/categories/all")
def get_all_categories(db: Session = Depends(get_db)):
    """Retorna todas las categorías de recetas disponibles"""
    from sqlalchemy import distinct
    categories = db.query(distinct(Recipe.category)).filter(
        Recipe.is_active == True
    ).all()
    return {"categories": [c[0] for c in categories]}


@router.get("/difficulties/all")
def get_all_difficulties():
    """Retorna las dificultades disponibles"""
    return {"difficulties": ["fácil", "media", "difícil"]}
