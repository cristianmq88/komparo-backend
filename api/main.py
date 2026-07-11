"""
api/main.py — Komparo API completa

Endpoints:
- Auth: register, login, me
- Lists: CRUD de cestas
- Items: añadir/quitar productos
- Recipes: catálogo de recetas
- Products: búsqueda y comparativa
- Supermarkets: info de los 8 súper
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr

from db.database import engine, get_db, Base
from db.models import User, ShoppingList, ListItem, Recipe
from api.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES,
    set_auth_cookie, clear_auth_cookie,
)
from api.endpoints_prices import router as prices_router, admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear tablas al arrancar
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas de BD creadas")
except Exception as e:
    logger.warning(f"⚠️ Error creando tablas: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Komparo API",
    description="API completa para Komparo - Comparador de precios Madrid",
    version="2.0.0",
)

# La web se sirve desde el mismo origen que la API (ver Dockerfile: la SPA se
# monta en "/"), por lo que la cookie de sesión HttpOnly viaja sin necesidad de
# credenciales CORS. Mantenemos allow_origins="*" con allow_credentials=False
# porque los navegadores rechazan la combinación "*" + credenciales.
#
# ⚠️ Si algún día despliegas la web en un origen DISTINTO al de la API, cambia
# esto por una lista explícita de orígenes y allow_credentials=True, y ajusta la
# cookie a SameSite="none"; Secure (ver api/auth.py) para que se envíe cross-site.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Registrar routers de scrapers (precios reales)
app.include_router(prices_router)
app.include_router(admin_router)


# ──────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=128)
    name: constr(min_length=1, max_length=120)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    is_premium: bool
    phone: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=120)] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: constr(min_length=6, max_length=128)


class AccountDelete(BaseModel):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ListCreate(BaseModel):
    name: str
    emoji: Optional[str] = "🛒"


class ItemCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    is_white_label: bool = False
    quantity: int = 1
    notes: Optional[str] = None


class ItemOut(BaseModel):
    id: str
    name: str
    brand: Optional[str]
    is_white_label: bool
    quantity: int
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class ListOut(BaseModel):
    id: str
    name: str
    emoji: str
    items: List[ItemOut] = []
    
    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# ROOT
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api")
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

@app.post("/auth/register", response_model=Token, tags=["auth"])
def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Registrar nueva cuenta"""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(400, "Email ya registrado")

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        {"sub": user.id},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    set_auth_cookie(response, token)
    return Token(access_token=token, token_type="bearer", user=UserOut.from_orm(user))


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login con email/password"""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Email o contraseña incorrectos")

    token = create_access_token(
        {"sub": user.id},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    set_auth_cookie(response, token)
    return Token(access_token=token, token_type="bearer", user=UserOut.from_orm(user))


@app.post("/auth/logout", tags=["auth"])
def logout(response: Response):
    """Cerrar sesión: elimina la cookie de sesión."""
    clear_auth_cookie(response)
    return {"message": "Sesión cerrada"}


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def get_me(user: User = Depends(get_current_user)):
    """Obtener mi perfil"""
    return user


@app.put("/auth/me", response_model=UserOut, tags=["auth"])
def update_me(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar datos del perfil (nombre, teléfono, ciudad, CP)."""
    updates = data.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/change-password", tags=["auth"])
def change_password(
    data: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambiar la contraseña verificando la actual."""
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(400, "La contraseña actual no es correcta")
    if data.current_password == data.new_password:
        raise HTTPException(400, "La nueva contraseña debe ser distinta")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente"}


@app.delete("/auth/me", tags=["auth"])
def delete_account(
    data: AccountDelete,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Eliminar la cuenta de forma permanente (derecho de supresión, RGPD).
    Borra el usuario y, en cascada, todas sus cestas y productos.
    """
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(400, "Contraseña incorrecta")
    db.delete(user)
    db.commit()
    clear_auth_cookie(response)
    return {"message": "Cuenta eliminada permanentemente"}


@app.get("/auth/me/export", tags=["auth"])
def export_my_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Exportar todos mis datos personales en formato JSON descargable
    (derecho de portabilidad, RGPD art. 20).
    """
    lists = db.query(ShoppingList).filter(ShoppingList.user_id == user.id).all()
    export = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "account": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "address": user.address,
            "city": user.city,
            "postal_code": user.postal_code,
            "is_premium": user.is_premium,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "lists": [
            {
                "id": lst.id,
                "name": lst.name,
                "emoji": lst.emoji,
                "created_at": lst.created_at.isoformat() if lst.created_at else None,
                "items": [
                    {
                        "name": item.name,
                        "brand": item.brand,
                        "is_white_label": item.is_white_label,
                        "quantity": item.quantity,
                        "notes": item.notes,
                    }
                    for item in lst.items
                ],
            }
            for lst in lists
        ],
    }
    payload = json.dumps(export, ensure_ascii=False, indent=2)
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="komparo-mis-datos.json"'},
    )


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


@app.get("/supermarkets", tags=["data"])
def list_supermarkets():
    return {"supermarkets": SUPERMARKETS}


# ──────────────────────────────────────────────────────────────────────────────
# PRODUCTS
# ──────────────────────────────────────────────────────────────────────────────
# La búsqueda y la comparativa de precios REALES viven en api/endpoints_prices.py
# (rutas /products/real/*), pobladas por los scrapers. Los antiguos endpoints de
# demostración con precios inventados se retiraron antes del lanzamiento público.


# ──────────────────────────────────────────────────────────────────────────────
# SHOPPING LISTS (Cestas)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/lists", response_model=List[ListOut], tags=["lists"])
def get_my_lists(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mis cestas"""
    return db.query(ShoppingList).filter(ShoppingList.user_id == user.id).all()


@app.get("/lists/{list_id}", response_model=ListOut, tags=["lists"])
def get_list(
    list_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Una cesta concreta"""
    lst = db.query(ShoppingList).filter(
        ShoppingList.id == list_id,
        ShoppingList.user_id == user.id
    ).first()
    if not lst:
        raise HTTPException(404, "Cesta no encontrada")
    return lst


@app.post("/lists", response_model=ListOut, tags=["lists"])
def create_list(
    data: ListCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva cesta"""
    new_list = ShoppingList(user_id=user.id, name=data.name, emoji=data.emoji)
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list


@app.delete("/lists/{list_id}", tags=["lists"])
def delete_list(
    list_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar cesta"""
    lst = db.query(ShoppingList).filter(
        ShoppingList.id == list_id,
        ShoppingList.user_id == user.id
    ).first()
    if not lst:
        raise HTTPException(404, "Cesta no encontrada")
    db.delete(lst)
    db.commit()
    return {"deleted": True}


@app.post("/lists/{list_id}/items", response_model=ItemOut, tags=["lists"])
def add_item(
    list_id: str,
    data: ItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Añadir producto a cesta"""
    lst = db.query(ShoppingList).filter(
        ShoppingList.id == list_id,
        ShoppingList.user_id == user.id
    ).first()
    if not lst:
        raise HTTPException(404, "Cesta no encontrada")
    
    item = ListItem(list_id=list_id, **data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/lists/{list_id}/items/{item_id}", tags=["lists"])
def remove_item(
    list_id: str,
    item_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Quitar producto de cesta"""
    item = db.query(ListItem).filter(
        ListItem.id == item_id,
        ListItem.list_id == list_id
    ).first()
    if not item:
        raise HTTPException(404, "Producto no encontrado")
    db.delete(item)
    db.commit()
    return {"deleted": True}


# La comparativa de precios REALES de una cesta vive en api/endpoints_prices.py
# (POST /products/real/compare-list), que es la que usa la web. El antiguo
# /lists/{id}/compare con precios inventados se retiró antes del lanzamiento.


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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
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
        ]
    },
]


@app.get("/recipes", tags=["recipes"])
def get_recipes(category: Optional[str] = None, difficulty: Optional[str] = None):
    """Listar recetas con filtros opcionales"""
    recipes = DEMO_RECIPES
    if category:
        recipes = [r for r in recipes if r["category"] == category]
    if difficulty:
        recipes = [r for r in recipes if r["difficulty"] == difficulty]
    return {"recipes": recipes, "total": len(recipes)}


@app.get("/recipes/{recipe_id}", tags=["recipes"])
def get_recipe(recipe_id: str):
    """Detalle de una receta"""
    for recipe in DEMO_RECIPES:
        if recipe["id"] == recipe_id:
            return recipe
    raise HTTPException(404, "Receta no encontrada")


@app.post("/recipes/{recipe_id}/create-list", response_model=ListOut, tags=["recipes"])
def create_list_from_recipe(
    recipe_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear cesta automáticamente desde una receta"""
    recipe = None
    for r in DEMO_RECIPES:
        if r["id"] == recipe_id:
            recipe = r
            break
    
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")
    
    # Crear cesta nueva
    new_list = ShoppingList(
        user_id=user.id,
        name=recipe["title"],
        emoji="🍳"
    )
    db.add(new_list)
    db.flush()
    
    # Añadir cada ingrediente
    for ing in recipe["ingredients"]:
        full_name = f"{ing['quantity']} {ing['unit']} {ing['name']}"
        item = ListItem(
            list_id=new_list.id,
            name=full_name,
            quantity=1,
            notes=f"De receta: {recipe['title']}"
        )
        db.add(item)
    
    db.commit()
    db.refresh(new_list)
    return new_list


# ──────────────────────────────────────────────────────────────────────────────
# STARTUP
# ──────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Komparo API v2.0 iniciada")
    db_url = os.getenv("DATABASE_URL", "")
    if "postgres" in db_url:
        logger.info("✅ PostgreSQL conectada")
    else:
        logger.warning("⚠️ Sin PostgreSQL - usando SQLite local")

    if not os.getenv("SECRET_KEY"):
        logger.warning(
            "🚨 SECRET_KEY no configurada: los tokens se firman con la clave "
            "por defecto (INSEGURO en producción). Añade SECRET_KEY al entorno."
        )

    # Arrancar el planificador de scrapers (scrapeo real automático).
    try:
        from scrapers.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning(f"⚠️ No se pudo arrancar el planificador: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# FRONTEND (SPA)
# ──────────────────────────────────────────────────────────────────────────────
# Si existe la web compilada (frontend/dist), FastAPI la sirve directamente.
# Así un único despliegue ofrece API + web en la misma URL (ideal para móvil).
# Las rutas de la API se declaran arriba, por lo que tienen prioridad.

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


class SPAStaticFiles(StaticFiles):
    """StaticFiles que devuelve index.html en rutas no encontradas (SPA)."""

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


if os.path.isdir(FRONTEND_DIST):
    app.mount("/", SPAStaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
    logger.info("✅ Frontend servido desde frontend/dist")
else:
    logger.info("ℹ️ frontend/dist no encontrado - API en modo solo-backend")
