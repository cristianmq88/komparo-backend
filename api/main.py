"""
api/main.py — FastAPI: punto de entrada de la API REST

Endpoints principales:
  POST /auth/register          → crear cuenta
  POST /auth/login             → obtener JWT
  GET  /products/search        → buscar productos en todos los supers
  GET  /products/{id}/prices   → historial de precios de un producto
  POST /lists                  → crear lista de la compra
  GET  /lists/{id}/compare     → calcular total por supermercado
  POST /lists/{id}/share       → compartir lista con otro usuario
  GET  /supermarkets           → info de los 8 supermercados
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import logging

from db import schemas, crud, models
from db.database import get_db, engine
from .auth import (
    authenticate_user, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

# Crear tablas al arrancar
models.Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SuperApp API",
    description="Comparador de precios en tiempo real — 8 supermercados de Madrid",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # en producción: lista de dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Crear cuenta nueva"""
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(400, "Email ya registrado")
    return crud.create_user(db, user)


@app.post("/auth/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login → devuelve JWT"""
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


# ── SUPERMERCADOS ─────────────────────────────────────────────────────────────

@app.get("/supermarkets", response_model=list[schemas.SupermarketOut])
def list_supermarkets(db: Session = Depends(get_db)):
    """Lista los 8 supermercados con info básica"""
    return crud.get_supermarkets(db)


# ── PRODUCTOS ─────────────────────────────────────────────────────────────────

@app.get("/products/search", response_model=list[schemas.ProductSearchResult])
def search_products(
    q:              str,
    category:       Optional[str] = None,
    supermarket_id: Optional[str] = None,
    limit:          int = 20,
    db: Session = Depends(get_db)
):
    """
    Busca productos en todos los supermercados.
    Devuelve resultados agrupados por producto normalizado,
    con el precio de cada super disponible.

    Ejemplo: GET /products/search?q=leche+semidesnatada
    → Leche semidesnatada: Mercadona 0,84€ | Alcampo 0,88€ | Lidl 0,86€ ...
    """
    return crud.search_normalized_products(db, q, category, supermarket_id, limit)


@app.get("/products/{product_id}/prices", response_model=schemas.ProductWithPrices)
def get_product_prices(product_id: str, db: Session = Depends(get_db)):
    """
    Devuelve el producto con precios actuales en todos los supermercados
    y el historial de los últimos 30 días.
    """
    result = crud.get_product_with_all_prices(db, product_id)
    if not result:
        raise HTTPException(404, "Producto no encontrado")
    return result


# ── LISTAS DE LA COMPRA ───────────────────────────────────────────────────────

@app.get("/lists", response_model=list[schemas.ShoppingListOut])
def get_my_lists(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Todas las listas del usuario (propias + compartidas)"""
    return crud.get_user_lists(db, current_user.id)


@app.post("/lists", response_model=schemas.ShoppingListOut, status_code=201)
def create_list(
    data: schemas.ShoppingListCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva lista"""
    return crud.create_shopping_list(db, current_user.id, data)


@app.post("/lists/{list_id}/items", response_model=schemas.ListItemOut, status_code=201)
def add_item(
    list_id: str,
    item:    schemas.ListItemCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Añadir producto a la lista.
    El sistema hace fuzzy-match del nombre con los productos de todos los supers.
    """
    the_list = crud.get_list(db, list_id, current_user.id)
    if not the_list:
        raise HTTPException(404, "Lista no encontrada")
    return crud.add_item_to_list(db, list_id, item)


@app.delete("/lists/{list_id}/items/{item_id}", status_code=204)
def remove_item(
    list_id: str,
    item_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    the_list = crud.get_list(db, list_id, current_user.id)
    if not the_list:
        raise HTTPException(404, "Lista no encontrada")
    crud.remove_item(db, item_id)


@app.get("/lists/{list_id}/compare", response_model=schemas.ListComparison)
def compare_list(
    list_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⭐ ENDPOINT PRINCIPAL DE LA APP ⭐

    Calcula el coste total de la lista en cada supermercado
    y devuelve el ranking de más barato a más caro.

    Respuesta:
    {
      "list_name": "Compra semanal",
      "total_items": 12,
      "ranking": [
        {
          "supermarket": "Alcampo",
          "total": 34.56,
          "savings_vs_most_expensive": 8.20,
          "items_available": 11,
          "items_missing": 1,
          "items": [
            { "name": "Leche semidesnatada 1L", "price": 0.88, "available": true },
            ...
          ]
        },
        ...
      ],
      "cheapest_supermarket": "Alcampo",
      "most_expensive_supermarket": "El Corte Inglés"
    }
    """
    the_list = crud.get_list(db, list_id, current_user.id)
    if not the_list:
        raise HTTPException(404, "Lista no encontrada")
    return crud.compare_list_prices(db, list_id)


# ── COMPARTIR LISTA ───────────────────────────────────────────────────────────

@app.post("/lists/{list_id}/share", response_model=schemas.ListShareOut, status_code=201)
def share_list(
    list_id:    str,
    share_data: schemas.ListShareCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compartir la lista con otro usuario por email.
    El destinatario verá la lista en su app y puede editarla si can_edit=True.
    """
    the_list = crud.get_list(db, list_id, current_user.id)
    if not the_list:
        raise HTTPException(404, "Lista no encontrada o sin permisos")

    target_user = crud.get_user_by_email(db, share_data.email)
    if not target_user:
        raise HTTPException(404, f"Usuario {share_data.email} no encontrado")

    if target_user.id == current_user.id:
        raise HTTPException(400, "No puedes compartir contigo mismo")

    return crud.share_list(db, list_id, target_user.id, share_data.can_edit)


@app.delete("/lists/{list_id}/share/{user_id}", status_code=204)
def unshare_list(
    list_id:  str,
    user_id:  str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revocar acceso compartido"""
    the_list = crud.get_list(db, list_id, current_user.id)
    if not the_list:
        raise HTTPException(404, "Lista no encontrada")
    crud.remove_share(db, list_id, user_id)


# ── SCHEDULER manual ─────────────────────────────────────────────────────────

@app.post("/admin/scrape/{supermarket_id}", status_code=202)
def trigger_scrape(supermarket_id: str):
    """
    Lanza manualmente el scraping de un supermercado (solo para testing/admin).
    En producción proteger con API key.
    """
    from scheduler.tasks import scrape_supermarket
    task = scrape_supermarket.delay(supermarket_id)
    return {"task_id": task.id, "status": "queued"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": "2026-05-14"}
