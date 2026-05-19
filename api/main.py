"""
api/main.py — Komparo API

Endpoints:
- Auth: register, login, me
- Lists: CRUD de cestas + comparativa
- Items: añadir/quitar productos
- Recipes: catálogo de recetas
- Products: búsqueda y comparativa
- Supermarkets: info de los 8 súper
"""
import hashlib
import logging
import os
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session, selectinload

from api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from api.endpoints_prices import admin_router, lists_router, router as prices_router
from db.database import Base, engine, get_db
from db.models import ListItem, Recipe, ShoppingList, User  # noqa: F401 (Recipe usado por create_all)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# LIFESPAN
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas de BD creadas")
    except Exception as e:
        logger.warning(f"⚠️ Error creando tablas: {e}")

    db_url = os.getenv("DATABASE_URL", "")
    if "postgres" in db_url:
        logger.info("✅ PostgreSQL conectada")
    else:
        logger.warning("⚠️ Sin PostgreSQL - usando SQLite local")

    logger.info("🚀 Komparo API v2.0 iniciada")
    yield


app = FastAPI(
    title="Komparo API",
    description="API completa para Komparo - Comparador de precios Madrid",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS: configurable vía env var; por defecto solo localhost en dev.
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prices_router)
app.include_router(lists_router)
app.include_router(admin_router)


# ──────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    is_premium: bool


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    emoji: Optional[str] = "🛒"


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: Optional[str] = None
    is_white_label: bool = False
    quantity: int = Field(1, ge=1, le=999)
    notes: Optional[str] = None


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    brand: Optional[str]
    is_white_label: bool
    quantity: int
    notes: Optional[str]


class ListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    emoji: str
    items: List[ItemOut] = []


# ──────────────────────────────────────────────────────────────────────────────
# ROOT
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "app": "Komparo API",
        "version": "2.0.0",
        "status": "running",
        "message": "Listas que comparan, decisiones que ahorran",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ──────────────────────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────────────────────

def _issue_token(user: User) -> Token:
    token = create_access_token(
        {"sub": user.id},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@app.post("/auth/register", response_model=Token, tags=["auth"])
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Registrar nueva cuenta."""
    if db.query(User.id).filter(User.email == data.email).first():
        raise HTTPException(400, "Email ya registrado")

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token(user)


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login con email/password."""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Email o contraseña incorrectos")
    return _issue_token(user)


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def get_me(user: User = Depends(get_current_user)):
    return user


# ──────────────────────────────────────────────────────────────────────────────
# SUPERMARKETS
# ──────────────────────────────────────────────────────────────────────────────

SUPERMARKETS = [
    {"id": "mercadona", "name": "Mercadona", "color": "#0E8C5A"},
    {"id": "carrefour", "name": "Carrefour", "color": "#004E9A"},
    {"id": "alcampo", "name": "Alcampo", "color": "#1E4296"},
    {"id": "dia", "name": "Dia", "color": "#E30613"},
    {"id": "lidl", "name": "Lidl", "color": "#0050AA"},
    {"id": "aldi", "name": "Aldi", "color": "#00529B"},
    {"id": "ahorramas", "name": "Ahorramas", "color": "#FF6B00"},
    {"id": "corteingles", "name": "El Corte Inglés", "color": "#006E42"},
]
_SUPERMARKET_IDS = [s["id"] for s in SUPERMARKETS]


@app.get("/supermarkets", tags=["data"])
def list_supermarkets():
    return {"supermarkets": SUPERMARKETS}


# ──────────────────────────────────────────────────────────────────────────────
# PRODUCTS (demo data — los scrapers reales viven en /products/real/*)
# ──────────────────────────────────────────────────────────────────────────────

DEMO_PRODUCTS = {
    "leche": [{"name": "Leche semidesnatada 1L", "prices": {"mercadona": 0.84, "alcampo": 0.88, "lidl": 0.86, "carrefour": 0.92, "dia": 0.89, "aldi": 0.85, "ahorramas": 0.91, "corteingles": 1.05}}],
    "pan": [{"name": "Pan de molde integral", "prices": {"mercadona": 1.45, "alcampo": 1.39, "lidl": 1.29, "carrefour": 1.55, "dia": 1.42, "aldi": 1.35, "ahorramas": 1.48, "corteingles": 1.85}}],
    "huevos": [{"name": "Huevos M docena", "prices": {"mercadona": 2.15, "alcampo": 2.05, "lidl": 1.95, "carrefour": 2.25, "dia": 2.10, "aldi": 1.99, "ahorramas": 2.20, "corteingles": 2.85}}],
    "pollo": [{"name": "Pechuga pollo 1kg", "prices": {"mercadona": 5.99, "alcampo": 5.49, "lidl": 5.79, "carrefour": 6.25, "dia": 5.89, "aldi": 5.69, "ahorramas": 6.15, "corteingles": 7.99}}],
    "aceite": [{"name": "Aceite oliva VE 1L", "prices": {"mercadona": 8.75, "alcampo": 7.95, "lidl": 8.20, "carrefour": 9.10, "dia": 8.40, "aldi": 8.15, "ahorramas": 8.95, "corteingles": 10.50}}],
    "yogur": [{"name": "Yogur natural pack 4", "prices": {"mercadona": 1.20, "alcampo": 1.15, "lidl": 1.10, "carrefour": 1.35, "dia": 1.22, "aldi": 1.12, "ahorramas": 1.30, "corteingles": 1.65}}],
}


def _stable_hash(text: str, modulo: int) -> int:
    """Hash determinista (`hash()` cambia entre procesos en Python)."""
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def _fallback_prices(name: str) -> dict[str, float]:
    """Precios fake estables para productos no encontrados en demo."""
    return {sm: round(1.5 + _stable_hash(name + sm, 50) / 10, 2) for sm in _SUPERMARKET_IDS}


def _lookup_demo_prices(name: str) -> dict[str, float]:
    """Busca un producto demo por palabra clave, o devuelve precios fallback."""
    name_lower = name.lower()
    for keyword, products in DEMO_PRODUCTS.items():
        if keyword in name_lower:
            return products[0]["prices"]
    return _fallback_prices(name)


@app.get("/products/search", tags=["data"])
def search_products(q: str = ""):
    """Buscar productos (demo data)."""
    if not q:
        return {"products": [], "message": "Especifica un parámetro q"}

    q_lower = q.lower()
    results = [
        product
        for keyword, products in DEMO_PRODUCTS.items()
        if keyword in q_lower or q_lower in keyword
        for product in products
    ]
    if not results:
        results = [{"name": q.title(), "prices": _fallback_prices(q)}]
    return {"query": q, "products": results}


# ──────────────────────────────────────────────────────────────────────────────
# SHOPPING LISTS (Cestas)
# ──────────────────────────────────────────────────────────────────────────────

def _get_owned_list(db: Session, list_id: str, user: User, eager_items: bool = False) -> ShoppingList:
    query = db.query(ShoppingList)
    if eager_items:
        query = query.options(selectinload(ShoppingList.items))
    lst = query.filter(
        ShoppingList.id == list_id, ShoppingList.user_id == user.id
    ).first()
    if not lst:
        raise HTTPException(404, "Cesta no encontrada")
    return lst


@app.get("/lists", response_model=List[ListOut], tags=["lists"])
def get_my_lists(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ShoppingList)
        .options(selectinload(ShoppingList.items))
        .filter(ShoppingList.user_id == user.id)
        .all()
    )


@app.post("/lists", response_model=ListOut, tags=["lists"])
def create_list(
    data: ListCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_list = ShoppingList(user_id=user.id, name=data.name, emoji=data.emoji)
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list


@app.delete("/lists/{list_id}", tags=["lists"])
def delete_list(
    list_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lst = _get_owned_list(db, list_id, user)
    db.delete(lst)
    db.commit()
    return {"deleted": True}


@app.post("/lists/{list_id}/items", response_model=ItemOut, tags=["lists"])
def add_item(
    list_id: str,
    data: ItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_list(db, list_id, user)
    item = ListItem(list_id=list_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/lists/{list_id}/items/{item_id}", tags=["lists"])
def remove_item(
    list_id: str,
    item_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_list(db, list_id, user)
    item = db.query(ListItem).filter(
        ListItem.id == item_id, ListItem.list_id == list_id
    ).first()
    if not item:
        raise HTTPException(404, "Producto no encontrado")
    db.delete(item)
    db.commit()
    return {"deleted": True}


@app.get("/lists/{list_id}/compare", tags=["lists"])
def compare_list(
    list_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Comparar precio de cesta en los 8 súper (demo data)."""
    lst = _get_owned_list(db, list_id, user, eager_items=True)

    totals = {sm_id: 0.0 for sm_id in _SUPERMARKET_IDS}
    for item in lst.items:
        prices = _lookup_demo_prices(item.name)
        for sm_id, price in prices.items():
            totals[sm_id] += price * item.quantity

    ranking = sorted(
        (
            {
                "supermarket": sm["id"],
                "name": sm["name"],
                "color": sm["color"],
                "total": round(totals[sm["id"]], 2),
            }
            for sm in SUPERMARKETS
        ),
        key=lambda x: x["total"],
    )

    return {
        "list_id": list_id,
        "list_name": lst.name,
        "items_count": len(lst.items),
        "ranking": ranking,
        "cheapest": ranking[0] if ranking else None,
        "savings": (
            round(ranking[-1]["total"] - ranking[0]["total"], 2)
            if len(ranking) > 1 else 0
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# RECIPES
# ──────────────────────────────────────────────────────────────────────────────

DEMO_RECIPES = [
    {
        "id": "recipe_1",
        "title": "Espaguetis a la carbonara",
        "description": "Pasta italiana clásica cremosa",
        "image_url": "https://via.placeholder.com/300x200?text=Carbonara",
        "servings": 4,
        "time_minutes": 20,
        "difficulty": "fácil",
        "category": "platos-principales",
        "ingredients": [
            {"name": "espaguetis", "quantity": "400", "unit": "g"},
            {"name": "huevos", "quantity": "4", "unit": "ud"},
            {"name": "bacon", "quantity": "200", "unit": "g"},
            {"name": "queso parmesano", "quantity": "100", "unit": "g"},
        ],
    },
    {
        "id": "recipe_2",
        "title": "Salmón a la mantequilla",
        "description": "Salmón tierno y jugoso",
        "image_url": "https://via.placeholder.com/300x200?text=Salmon",
        "servings": 4,
        "time_minutes": 25,
        "difficulty": "fácil",
        "category": "pescados",
        "ingredients": [
            {"name": "salmón fresco", "quantity": "800", "unit": "g"},
            {"name": "mantequilla", "quantity": "100", "unit": "g"},
            {"name": "limón", "quantity": "2", "unit": "ud"},
        ],
    },
    {
        "id": "recipe_3",
        "title": "Pollo al curry",
        "description": "Curry cremoso con pollo tierno",
        "image_url": "https://via.placeholder.com/300x200?text=Curry",
        "servings": 4,
        "time_minutes": 40,
        "difficulty": "media",
        "category": "carnes",
        "ingredients": [
            {"name": "pechuga de pollo", "quantity": "800", "unit": "g"},
            {"name": "curry en polvo", "quantity": "3", "unit": "cucharadas"},
            {"name": "leche de coco", "quantity": "400", "unit": "ml"},
            {"name": "cebolla", "quantity": "2", "unit": "ud"},
        ],
    },
    {
        "id": "recipe_4",
        "title": "Tortilla de patatas",
        "description": "El clásico español",
        "image_url": "https://via.placeholder.com/300x200?text=Tortilla",
        "servings": 6,
        "time_minutes": 35,
        "difficulty": "media",
        "category": "platos-principales",
        "ingredients": [
            {"name": "patatas", "quantity": "1", "unit": "kg"},
            {"name": "huevos", "quantity": "6", "unit": "ud"},
            {"name": "cebolla", "quantity": "1", "unit": "ud"},
            {"name": "aceite oliva", "quantity": "200", "unit": "ml"},
        ],
    },
    {
        "id": "recipe_5",
        "title": "Gazpacho andaluz",
        "description": "Sopa fría refrescante",
        "image_url": "https://via.placeholder.com/300x200?text=Gazpacho",
        "servings": 4,
        "time_minutes": 15,
        "difficulty": "fácil",
        "category": "platos-principales",
        "ingredients": [
            {"name": "tomate", "quantity": "1000", "unit": "g"},
            {"name": "pepino", "quantity": "1", "unit": "ud"},
            {"name": "pimiento rojo", "quantity": "1", "unit": "ud"},
            {"name": "ajo", "quantity": "2", "unit": "dientes"},
        ],
    },
    {
        "id": "recipe_6",
        "title": "Tarta de chocolate",
        "description": "Postre clásico y delicioso",
        "image_url": "https://via.placeholder.com/300x200?text=Tarta",
        "servings": 8,
        "time_minutes": 45,
        "difficulty": "media",
        "category": "postres",
        "ingredients": [
            {"name": "chocolate negro", "quantity": "300", "unit": "g"},
            {"name": "mantequilla", "quantity": "200", "unit": "g"},
            {"name": "huevos", "quantity": "6", "unit": "ud"},
            {"name": "azúcar", "quantity": "200", "unit": "g"},
            {"name": "harina", "quantity": "100", "unit": "g"},
        ],
    },
]
_RECIPES_BY_ID = {r["id"]: r for r in DEMO_RECIPES}


@app.get("/recipes", tags=["recipes"])
def get_recipes(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
):
    recipes = [
        r for r in DEMO_RECIPES
        if (not category or r["category"] == category)
        and (not difficulty or r["difficulty"] == difficulty)
    ]
    return {"recipes": recipes, "total": len(recipes)}


@app.get("/recipes/{recipe_id}", tags=["recipes"])
def get_recipe(recipe_id: str):
    recipe = _RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")
    return recipe


@app.post("/recipes/{recipe_id}/create-list", response_model=ListOut, tags=["recipes"])
def create_list_from_recipe(
    recipe_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear cesta automáticamente desde una receta."""
    recipe = _RECIPES_BY_ID.get(recipe_id)
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")

    new_list = ShoppingList(
        user_id=user.id,
        name=recipe["title"],
        emoji="🍳",
    )
    db.add(new_list)
    db.flush()

    for ing in recipe["ingredients"]:
        db.add(ListItem(
            list_id=new_list.id,
            name=f"{ing['quantity']} {ing['unit']} {ing['name']}",
            quantity=1,
            notes=f"De receta: {recipe['title']}",
        ))

    db.commit()
    db.refresh(new_list)
    return new_list
