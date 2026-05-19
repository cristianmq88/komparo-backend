"""
api/main.py — Komparo API

Endpoints:
- Auth: register, login, me, verify-email, resend-verification,
        forgot-password, reset-password
- Lists: CRUD de cestas + comparativa
- Items: añadir/quitar productos
- Recipes: catálogo de recetas (sembrado en BD)
- Products: búsqueda y comparativa
- Supermarkets: info de los 8 súper
"""
import hashlib
import logging
import os
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    MAX_FAILED_LOGINS,
    PASSWORD_RESET_TOKEN_MINUTES,
    VERIFICATION_TOKEN_HOURS,
    create_access_token,
    generate_opaque_token,
    get_current_user,
    hash_password,
    hash_token,
    is_locked_out,
    register_failed_login,
    reset_failed_logins,
    verify_password,
)
from api.email_service import send_password_reset_email, send_verification_email
from api.endpoints_prices import admin_router, lists_router, router as prices_router
from api.rate_limit import check_rate_limit
from db.database import (
    Base, engine, ensure_schema_updates, get_db, seed_recipes_if_empty, utcnow,
)
from db.models import ListItem, PasswordResetToken, Recipe, ShoppingList, User

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


# ──────────────────────────────────────────────────────────────────────────────
# LIFESPAN
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        ensure_schema_updates()
        seed_recipes_if_empty()
        logger.info("✅ Esquema BD listo")
    except Exception as e:
        logger.warning(f"⚠️ Error preparando BD: {e}")

    db_url = os.getenv("DATABASE_URL", "")
    if "postgres" in db_url:
        logger.info("✅ PostgreSQL conectada")
    else:
        logger.warning("⚠️ Sin PostgreSQL - usando SQLite local")

    logger.info("🚀 Komparo API v2.1 iniciada")
    yield


app = FastAPI(
    title="Komparo API",
    description="API completa para Komparo - Comparador de precios Madrid",
    version="2.1.0",
    lifespan=lifespan,
)

_cors_origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
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
    email_verified: bool
    phone: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    city: Optional[str] = Field(None, max_length=120)
    postal_code: Optional[str] = Field(None, max_length=10)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class DeleteAccountIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=10)


class ResendVerificationIn(BaseModel):
    email: EmailStr


class MessageOut(BaseModel):
    message: str


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
        "version": "2.1.0",
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
def register(
    data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """Registra una cuenta nueva y envía email de verificación."""
    check_rate_limit(request, "register", max_requests=5, window_seconds=3600)

    if db.query(User.id).filter(User.email == data.email).first():
        raise HTTPException(400, "Email ya registrado")

    raw_token = generate_opaque_token()
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
        verification_token=hash_token(raw_token),
        verification_expires=utcnow() + timedelta(hours=VERIFICATION_TOKEN_HOURS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    send_verification_email(user.email, user.name, raw_token)
    return _issue_token(user)


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login con email/password. Bloquea tras N intentos fallidos."""
    check_rate_limit(request, "login", max_requests=20, window_seconds=60)

    user = db.query(User).filter(User.email == form.username).first()

    # No revelar si el email existe
    if not user:
        raise HTTPException(401, "Email o contraseña incorrectos")

    if is_locked_out(user):
        remaining = int((user.lockout_until - utcnow()).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Cuenta bloqueada temporalmente. Reintenta en {remaining} minutos.",
        )

    if not verify_password(form.password, user.hashed_password):
        register_failed_login(user)
        db.commit()
        remaining_attempts = MAX_FAILED_LOGINS - (user.failed_login_count or 0)
        if user.lockout_until and user.lockout_until > utcnow():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos. Cuenta bloqueada 15 minutos.",
            )
        raise HTTPException(
            401,
            f"Email o contraseña incorrectos. Intentos restantes: {remaining_attempts}",
        )

    reset_failed_logins(user)
    db.commit()
    return _issue_token(user)


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def get_me(user: User = Depends(get_current_user)):
    return user


@app.put("/auth/me", response_model=UserOut, tags=["auth"])
def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza el perfil del usuario autenticado."""
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        return user
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@app.put("/auth/password", response_model=MessageOut, tags=["auth"])
def change_password(
    data: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambia la contraseña del usuario autenticado."""
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(401, "La contraseña actual no es correcta")
    if data.new_password == data.current_password:
        raise HTTPException(400, "La nueva contraseña debe ser distinta")

    user.hashed_password = hash_password(data.new_password)
    reset_failed_logins(user)
    db.commit()
    return MessageOut(message="Contraseña actualizada correctamente")


@app.delete("/auth/me", response_model=MessageOut, tags=["auth"])
def delete_account(
    data: DeleteAccountIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Elimina la cuenta y todos sus datos (RGPD)."""
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Contraseña incorrecta")

    # Limpieza explícita de tokens de reset (no tienen cascade)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).delete(synchronize_session=False)

    # ShoppingList → ListItem ya tienen cascade="all, delete-orphan"
    db.delete(user)
    db.commit()
    return MessageOut(message="Cuenta eliminada")


@app.post("/auth/verify-email", response_model=MessageOut, tags=["auth"])
def verify_email(data: VerifyEmailIn, db: Session = Depends(get_db)):
    """Marca el email del usuario como verificado."""
    token_hash = hash_token(data.token)
    user = db.query(User).filter(User.verification_token == token_hash).first()
    if not user:
        raise HTTPException(400, "Token de verificación inválido")
    if user.verification_expires and user.verification_expires < utcnow():
        raise HTTPException(400, "El token ha caducado, pide otro")

    user.email_verified = True
    user.verification_token = None
    user.verification_expires = None
    db.commit()
    return MessageOut(message="Email verificado correctamente")


@app.post("/auth/resend-verification", response_model=MessageOut, tags=["auth"])
def resend_verification(
    data: ResendVerificationIn,
    request: Request,
    db: Session = Depends(get_db),
):
    """Reenvía el email de verificación. Respuesta neutra (no revela emails)."""
    check_rate_limit(request, "resend-verif", max_requests=3, window_seconds=3600)

    user = db.query(User).filter(User.email == data.email).first()
    neutral = MessageOut(message="Si el email existe, se ha enviado un nuevo enlace")
    if not user or user.email_verified:
        return neutral

    raw_token = generate_opaque_token()
    user.verification_token = hash_token(raw_token)
    user.verification_expires = utcnow() + timedelta(hours=VERIFICATION_TOKEN_HOURS)
    db.commit()

    send_verification_email(user.email, user.name, raw_token)
    return neutral


@app.post("/auth/forgot-password", response_model=MessageOut, tags=["auth"])
def forgot_password(
    data: ForgotPasswordIn,
    request: Request,
    db: Session = Depends(get_db),
):
    """Envía un email con enlace de restablecimiento. Respuesta neutra."""
    check_rate_limit(request, "forgot-pwd", max_requests=5, window_seconds=3600)

    user = db.query(User).filter(User.email == data.email).first()
    neutral = MessageOut(message="Si el email existe, se ha enviado un enlace")
    if not user:
        return neutral

    raw_token = generate_opaque_token()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_MINUTES),
    ))
    db.commit()

    send_password_reset_email(user.email, user.name, raw_token)
    return neutral


@app.post("/auth/reset-password", response_model=MessageOut, tags=["auth"])
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    """Establece una nueva contraseña a partir del token recibido por email."""
    token_hash = hash_token(data.token)
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )
    if not record or record.used or record.expires_at < utcnow():
        raise HTTPException(400, "Token inválido o caducado")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(400, "Token inválido")

    user.hashed_password = hash_password(data.new_password)
    record.used = True
    reset_failed_logins(user)
    db.commit()
    return MessageOut(message="Contraseña actualizada correctamente")


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
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def _fallback_prices(name: str) -> dict[str, float]:
    return {sm: round(1.5 + _stable_hash(name + sm, 50) / 10, 2) for sm in _SUPERMARKET_IDS}


def _lookup_demo_prices(name: str) -> dict[str, float]:
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
# SHOPPING LISTS
# ──────────────────────────────────────────────────────────────────────────────

def _get_owned_list(
    db: Session, list_id: str, user: User, eager_items: bool = False
) -> ShoppingList:
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
# RECIPES (servidas desde la BD)
# ──────────────────────────────────────────────────────────────────────────────

def _serialize_recipe(r: Recipe) -> dict:
    return {
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "image_url": r.image_url,
        "servings": r.servings,
        "time_minutes": r.time_minutes,
        "difficulty": r.difficulty,
        "category": r.category,
        "ingredients": r.ingredients or [],
        "instructions": r.instructions,
    }


@app.get("/recipes/categories", tags=["recipes"])
def list_recipe_categories(db: Session = Depends(get_db)):
    """Lista las categorías y dificultades disponibles."""
    cat_rows = db.query(Recipe.category, func.count(Recipe.id)).group_by(
        Recipe.category
    ).all()
    diff_rows = db.query(Recipe.difficulty, func.count(Recipe.id)).group_by(
        Recipe.difficulty
    ).all()
    return {
        "categories": [{"id": c, "count": n} for c, n in cat_rows if c],
        "difficulties": [{"id": d, "count": n} for d, n in diff_rows if d],
    }


@app.get("/recipes", tags=["recipes"])
def get_recipes(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Recipe)
    if category:
        query = query.filter(Recipe.category == category)
    if difficulty:
        query = query.filter(Recipe.difficulty == difficulty)
    recipes = query.order_by(Recipe.title.asc()).all()
    return {
        "recipes": [_serialize_recipe(r) for r in recipes],
        "total": len(recipes),
    }


@app.get("/recipes/{recipe_id}", tags=["recipes"])
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")
    return _serialize_recipe(recipe)


@app.post(
    "/recipes/{recipe_id}/create-list", response_model=ListOut, tags=["recipes"]
)
def create_list_from_recipe(
    recipe_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crear cesta automáticamente desde una receta."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, "Receta no encontrada")

    new_list = ShoppingList(
        user_id=user.id,
        name=recipe.title,
        emoji="🍳",
    )
    db.add(new_list)
    db.flush()

    for ing in recipe.ingredients or []:
        db.add(ListItem(
            list_id=new_list.id,
            name=f"{ing.get('quantity', '')} {ing.get('unit', '')} {ing.get('name', '')}".strip(),
            quantity=1,
            notes=f"De receta: {recipe.title}",
        ))

    db.commit()
    db.refresh(new_list)
    return new_list
