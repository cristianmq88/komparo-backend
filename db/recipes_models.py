"""
db/recipes_models.py - Modelos SQLAlchemy para recetas
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, Table, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
from db.models import Base


def gen_uuid():
    return str(uuid.uuid4())


class Recipe(Base):
    """Receta con ingredientes"""
    __tablename__ = "recipes"

    id              = Column(String(200), primary_key=True)  # "source_recipe_name"
    source          = Column(String(50), index=True)          # recetasderechupete, directo_al_paladar...
    title           = Column(String(300), nullable=False)
    url             = Column(String(500))
    description     = Column(Text)
    image_url       = Column(String(500))
    servings        = Column(Integer, default=4)
    time_minutes    = Column(Integer)
    difficulty      = Column(String(50))  # fácil, media, difícil
    category        = Column(String(100), index=True)
    ingredients     = Column(JSONB)  # [{"name": "...", "quantity": "...", "unit": "..."}]
    is_active       = Column(Boolean, default=True)
    last_updated    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    favorites       = relationship("UserRecipeFavorite", back_populates="recipe")
    used_in_lists   = relationship("ListFromRecipe", back_populates="recipe")

    __table_args__ = (
        Index("ix_recipe_source_category", "source", "category"),
        Index("ix_recipe_title", "title"),
    )


class UserRecipeFavorite(Base):
    """Recetas favoritas del usuario"""
    __tablename__ = "user_recipe_favorites"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    user_id         = Column(UUID, ForeignKey("users.id"), nullable=False)
    recipe_id       = Column(String(200), ForeignKey("recipes.id"), nullable=False)
    saved_at        = Column(DateTime, default=datetime.utcnow)

    recipe          = relationship("Recipe", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_fav"),
    )


class ListFromRecipe(Base):
    """Listas creadas a partir de recetas"""
    __tablename__ = "lists_from_recipes"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    list_id         = Column(UUID, ForeignKey("shopping_lists.id"), nullable=False)
    recipe_id       = Column(String(200), ForeignKey("recipes.id"), nullable=False)
    servings_used   = Column(Integer, default=4)  # Si la receta es para 4 pero cocinamos para 6
    created_at      = Column(DateTime, default=datetime.utcnow)

    recipe          = relationship("Recipe", back_populates="used_in_lists")


# ══════════════════════════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════════════════════════

from sqlalchemy.orm import Session

def load_recipes_from_json(db: Session, json_file: str = "recipes_database.json"):
    """Carga las recetas desde el JSON generado por el scraper"""
    import json
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for recipe_data in data.get("recipes", []):
            # Check if exists
            existing = db.query(Recipe).filter(Recipe.id == recipe_data["id"]).first()
            if existing:
                continue
            
            recipe = Recipe(
                id=recipe_data["id"],
                source=recipe_data["source"],
                title=recipe_data["title"],
                url=recipe_data["url"],
                description=recipe_data.get("description", ""),
                image_url=recipe_data.get("image_url", ""),
                servings=recipe_data.get("servings", 4),
                time_minutes=recipe_data.get("time_minutes"),
                difficulty=recipe_data.get("difficulty", "media"),
                category=recipe_data.get("category", "general"),
                ingredients=recipe_data.get("ingredients", []),
            )
            db.add(recipe)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error loading recipes: {e}")
        return False


def search_recipes(
    db: Session,
    query: str = "",
    category: str = "",
    difficulty: str = "",
    max_time: int = 60,
) -> list[Recipe]:
    """Busca recetas por título, categoría, dificultad y tiempo"""
    q = db.query(Recipe).filter(Recipe.is_active == True)
    
    if query:
        q = q.filter(Recipe.title.ilike(f"%{query}%"))
    if category:
        q = q.filter(Recipe.category == category)
    if difficulty:
        q = q.filter(Recipe.difficulty == difficulty)
    if max_time:
        q = q.filter(Recipe.time_minutes <= max_time)
    
    return q.limit(50).all()


def get_recipes_by_ingredients(
    db: Session,
    shopping_items: list[str],
    min_match: float = 0.3,
) -> list[tuple[Recipe, float]]:
    """
    Retorna recetas que coincidan con ingredientes de la lista de la compra.
    Retorna tuplas (receta, score_match).
    score_match va de 0 a 1.
    """
    recipes = db.query(Recipe).filter(Recipe.is_active == True).all()
    matches = []
    
    for recipe in recipes:
        # Calcular coincidencia
        recipe_ing_names = [ing.get("name", "").lower() for ing in recipe.ingredients or []]
        shopping_norm = [item.lower() for item in shopping_items]
        
        matches_count = 0
        for ing in recipe_ing_names:
            for item in shopping_norm:
                if ing in item or item in ing:
                    matches_count += 1
                    break
        
        if recipe_ing_names:
            score = matches_count / len(recipe_ing_names)
        else:
            score = 0
        
        if score >= min_match:
            matches.append((recipe, score))
    
    # Ordenar por score descendente
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def get_recipe_details(db: Session, recipe_id: str) -> Optional[Recipe]:
    """Obtiene una receta específica"""
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def save_favorite_recipe(db: Session, user_id: str, recipe_id: str):
    """Guarda una receta como favorita"""
    existing = db.query(UserRecipeFavorite).filter(
        UserRecipeFavorite.user_id == user_id,
        UserRecipeFavorite.recipe_id == recipe_id,
    ).first()
    
    if not existing:
        fav = UserRecipeFavorite(user_id=user_id, recipe_id=recipe_id)
        db.add(fav)
        db.commit()
        return True
    return False


def remove_favorite_recipe(db: Session, user_id: str, recipe_id: str):
    """Quita una receta de favoritos"""
    db.query(UserRecipeFavorite).filter(
        UserRecipeFavorite.user_id == user_id,
        UserRecipeFavorite.recipe_id == recipe_id,
    ).delete()
    db.commit()


def get_user_favorites(db: Session, user_id: str) -> list[Recipe]:
    """Obtiene las recetas favoritas del usuario"""
    favs = db.query(UserRecipeFavorite).filter(
        UserRecipeFavorite.user_id == user_id
    ).all()
    return [fav.recipe for fav in favs]
