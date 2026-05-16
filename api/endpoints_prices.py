"""
Nuevos endpoints para precios reales.
Añadir estos a tu main.py de FastAPI.

Endpoints añadidos:
- GET  /products/real/search?q=...    → Buscar productos reales
- GET  /products/{id}/prices          → Precios de un producto en todos los súper
- GET  /products/{id}/history         → Histórico de precios
- POST /lists/{id}/compare-real       → Comparativa con precios reales
- GET  /admin/scrapers/status         → Estado de los scrapers
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

# Imports del backend
from db.database import get_db
from api.auth import get_current_user
from db.models_prices import Product, CurrentPrice, PriceHistory, ScraperRun
from db.models import User, ShoppingList, ListItem
 

router = APIRouter(prefix="/products/real", tags=["real-prices"])


@router.get("/search")
def search_real_products(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db)
):
    """
    Busca productos reales en la BD por nombre.
    Devuelve los productos junto con sus precios en cada súper.
    """
    # Normalizar la query igual que hace el scraper
    normalized = q.lower().strip()
    
    products = db.query(Product).filter(
        or_(
            Product.normalized_name.ilike(f"%{normalized}%"),
            Product.name.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    results = []
    for product in products:
        prices = db.query(CurrentPrice).filter(
            CurrentPrice.product_id == product.id
        ).all()
        
        # Encontrar el más barato
        if prices:
            cheapest = min(prices, key=lambda p: float(p.price))
        else:
            cheapest = None
        
        results.append({
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "unit_size": float(product.unit_size) if product.unit_size else None,
            "unit_type": product.unit_type,
            "prices": [
                {
                    "supermarket": p.supermarket,
                    "price": float(p.price),
                    "price_per_unit": float(p.price_per_unit) if p.price_per_unit else None,
                    "in_stock": p.in_stock,
                    "last_seen": p.last_seen.isoformat() if p.last_seen else None
                }
                for p in prices
            ],
            "cheapest_supermarket": cheapest.supermarket if cheapest else None,
            "cheapest_price": float(cheapest.price) if cheapest else None
        })
    
    return {"query": q, "count": len(results), "products": results}


@router.get("/{product_id}/prices")
def get_product_prices(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Devuelve los precios de un producto en todos los supermercados."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    
    prices = db.query(CurrentPrice).filter(
        CurrentPrice.product_id == product.id
    ).all()
    
    return {
        "product": {
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "image_url": product.image_url
        },
        "prices": sorted([
            {
                "supermarket": p.supermarket,
                "price": float(p.price),
                "price_per_unit": float(p.price_per_unit) if p.price_per_unit else None,
                "in_stock": p.in_stock,
                "product_url": p.product_url,
                "last_seen": p.last_seen.isoformat()
            }
            for p in prices
        ], key=lambda x: x["price"])
    }


@router.get("/{product_id}/history")
def get_product_history(
    product_id: str,
    days: int = Query(30, le=90),
    db: Session = Depends(get_db)
):
    """Devuelve histórico de precios para gráficos."""
    since = datetime.utcnow() - timedelta(days=days)
    
    history = db.query(PriceHistory).filter(
        and_(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_at >= since
        )
    ).order_by(PriceHistory.recorded_at.asc()).all()
    
    # Agrupar por supermercado
    by_super = {}
    for h in history:
        if h.supermarket not in by_super:
            by_super[h.supermarket] = []
        by_super[h.supermarket].append({
            "date": h.recorded_at.isoformat(),
            "price": float(h.price)
        })
    
    return {"product_id": product_id, "days": days, "history": by_super}


@router.post("/compare-list")
def compare_list_with_real_prices(
    list_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Compara una cesta usando precios reales.
    Para cada item de la cesta, busca el producto más parecido
    en cada supermercado y suma los precios.
    """
    # Obtener la lista del usuario
    shopping_list = db.query(ShoppingList).filter(
        and_(
            ShoppingList.id == list_id,
            ShoppingList.user_id == user.id
        )
    ).first()
    
    if not shopping_list:
        raise HTTPException(404, "Lista no encontrada")
    
    if not shopping_list.items:
        return {"error": "Lista vacía"}
    
    # Para cada item, buscar el producto real
    supermarket_totals = {}  # {supermarket: total}
    item_breakdown = []
    
    for item in shopping_list.items:
        # Buscar producto similar
        normalized = item.name.lower().strip()
        product = db.query(Product).filter(
            or_(
                Product.normalized_name.ilike(f"%{normalized}%"),
                Product.name.ilike(f"%{item.name}%")
            )
        ).first()
        
        if not product:
            # No tenemos precios reales de este producto
            item_breakdown.append({
                "item_name": item.name,
                "quantity": item.quantity,
                "matched": False,
                "prices": {}
            })
            continue
        
        # Obtener precios en cada súper
        prices = db.query(CurrentPrice).filter(
            CurrentPrice.product_id == product.id
        ).all()
        
        item_prices = {}
        for p in prices:
            total = float(p.price) * item.quantity
            item_prices[p.supermarket] = {
                "unit_price": float(p.price),
                "total": round(total, 2)
            }
            # Acumular total
            supermarket_totals[p.supermarket] = supermarket_totals.get(p.supermarket, 0) + total
        
        item_breakdown.append({
            "item_name": item.name,
            "matched_product": product.name,
            "quantity": item.quantity,
            "matched": True,
            "prices": item_prices
        })
    
    # Ranking
    ranking = sorted(
        [{"supermarket": s, "total": round(t, 2)} for s, t in supermarket_totals.items()],
        key=lambda x: x["total"]
    )
    
    savings = 0
    if len(ranking) >= 2:
        savings = round(ranking[-1]["total"] - ranking[0]["total"], 2)
    
    return {
        "list_id": list_id,
        "list_name": shopping_list.name,
        "items": item_breakdown,
        "ranking": ranking,
        "savings": savings,
        "data_source": "real_prices"
    }


# ════════════════════════════════════════════════════════════════════
# ADMIN endpoints (solo para ti)
# ════════════════════════════════════════════════════════════════════

admin_router = APIRouter(prefix="/admin/scrapers", tags=["admin"])


@admin_router.get("/status")
def scrapers_status(db: Session = Depends(get_db)):
    """Estado de las últimas ejecuciones de cada scraper."""
    supermarkets = ["carrefour", "mercadona", "dia", "alcampo"]
    
    status = {}
    for sm in supermarkets:
        # Última ejecución
        last_run = db.query(ScraperRun).filter(
            ScraperRun.supermarket == sm
        ).order_by(ScraperRun.started_at.desc()).first()
        
        # Productos actuales
        product_count = db.query(func.count(CurrentPrice.id)).filter(
            CurrentPrice.supermarket == sm
        ).scalar()
        
        # Precio más reciente
        latest_price = db.query(CurrentPrice).filter(
            CurrentPrice.supermarket == sm
        ).order_by(CurrentPrice.last_seen.desc()).first()
        
        status[sm] = {
            "products_in_db": product_count,
            "last_scrape": last_run.started_at.isoformat() if last_run else None,
            "last_scrape_status": last_run.status if last_run else "never_run",
            "last_scrape_products": last_run.products_scraped if last_run else 0,
            "last_scrape_errors": last_run.errors if last_run else 0,
            "freshness_hours": (
                (datetime.utcnow() - latest_price.last_seen).total_seconds() / 3600
                if latest_price else None
            )
        }
    
    return {"scrapers": status, "checked_at": datetime.utcnow().isoformat()}
