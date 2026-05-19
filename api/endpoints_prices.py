"""
Endpoints de precios reales (alimentados por scrapers).

- GET  /products/real/search?q=...           Buscar productos reales
- GET  /products/real/{product_id}/prices    Precios en todos los súper
- GET  /products/real/{product_id}/history   Histórico de precios
- POST /lists/{list_id}/compare-real         Comparativa real de una cesta
- GET  /admin/scrapers/status                Estado de los scrapers
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, selectinload

from api.auth import get_current_user
from db.database import get_db
from db.models import ListItem, ShoppingList, User
from db.models_prices import CurrentPrice, PriceHistory, Product, ScraperRun

router = APIRouter(prefix="/products/real", tags=["real-prices"])
lists_router = APIRouter(prefix="/lists", tags=["real-prices"])
admin_router = APIRouter(prefix="/admin/scrapers", tags=["admin"])

SUPERMARKETS = ("carrefour", "mercadona", "dia", "alcampo")


def _serialize_price(p: CurrentPrice) -> dict:
    return {
        "supermarket": p.supermarket,
        "price": float(p.price),
        "price_per_unit": float(p.price_per_unit) if p.price_per_unit else None,
        "in_stock": p.in_stock,
        "product_url": p.product_url,
        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
    }


def _find_product(db: Session, name: str) -> Optional[Product]:
    """Busca un producto por nombre/normalizado."""
    normalized = name.lower().strip()
    return (
        db.query(Product)
        .filter(
            or_(
                Product.normalized_name.ilike(f"%{normalized}%"),
                Product.name.ilike(f"%{name}%"),
            )
        )
        .first()
    )


@router.get("/search")
def search_real_products(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
):
    """Busca productos reales por nombre y devuelve sus precios en cada súper."""
    normalized = q.lower().strip()

    products = (
        db.query(Product)
        .filter(
            or_(
                Product.normalized_name.ilike(f"%{normalized}%"),
                Product.name.ilike(f"%{q}%"),
            )
        )
        .limit(limit)
        .all()
    )

    # Bulk-load de precios para evitar N+1
    product_ids = [p.id for p in products]
    prices_by_product: dict[str, list[CurrentPrice]] = defaultdict(list)
    if product_ids:
        for cp in (
            db.query(CurrentPrice)
            .filter(CurrentPrice.product_id.in_(product_ids))
            .all()
        ):
            prices_by_product[cp.product_id].append(cp)

    results = []
    for product in products:
        prices = prices_by_product.get(product.id, [])
        cheapest = min(prices, key=lambda p: float(p.price)) if prices else None
        results.append({
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "unit_size": float(product.unit_size) if product.unit_size else None,
            "unit_type": product.unit_type,
            "prices": [_serialize_price(p) for p in prices],
            "cheapest_supermarket": cheapest.supermarket if cheapest else None,
            "cheapest_price": float(cheapest.price) if cheapest else None,
        })

    return {"query": q, "count": len(results), "products": results}


@router.get("/{product_id}/prices")
def get_product_prices(product_id: str, db: Session = Depends(get_db)):
    """Devuelve los precios de un producto en todos los supermercados."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Producto no encontrado")

    prices = (
        db.query(CurrentPrice)
        .filter(CurrentPrice.product_id == product.id)
        .all()
    )

    return {
        "product": {
            "id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "image_url": product.image_url,
        },
        "prices": sorted(
            (_serialize_price(p) for p in prices),
            key=lambda x: x["price"],
        ),
    }


@router.get("/{product_id}/history")
def get_product_history(
    product_id: str,
    days: int = Query(30, le=90),
    db: Session = Depends(get_db),
):
    """Histórico de precios agrupado por supermercado."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    history = (
        db.query(PriceHistory)
        .filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= since,
            )
        )
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )

    by_super: dict[str, list[dict]] = defaultdict(list)
    for h in history:
        by_super[h.supermarket].append({
            "date": h.recorded_at.isoformat(),
            "price": float(h.price),
        })

    return {"product_id": product_id, "days": days, "history": dict(by_super)}


@lists_router.post("/{list_id}/compare-real")
def compare_list_with_real_prices(
    list_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compara una cesta usando los precios reales más recientes."""
    shopping_list = (
        db.query(ShoppingList)
        .options(selectinload(ShoppingList.items))
        .filter(
            and_(ShoppingList.id == list_id, ShoppingList.user_id == user.id)
        )
        .first()
    )
    if not shopping_list:
        raise HTTPException(404, "Lista no encontrada")
    if not shopping_list.items:
        raise HTTPException(400, "Lista vacía")

    supermarket_totals: dict[str, float] = defaultdict(float)
    item_breakdown: list[dict] = []

    # Recolectamos los productos matcheados en una sola pasada
    matched_pairs: list[tuple[ListItem, Product]] = []
    for item in shopping_list.items:
        product = _find_product(db, item.name)
        if product:
            matched_pairs.append((item, product))
        else:
            item_breakdown.append({
                "item_name": item.name,
                "quantity": item.quantity,
                "matched": False,
                "prices": {},
            })

    if matched_pairs:
        product_ids = [p.id for _, p in matched_pairs]
        prices_by_product: dict[str, list[CurrentPrice]] = defaultdict(list)
        for cp in (
            db.query(CurrentPrice)
            .filter(CurrentPrice.product_id.in_(product_ids))
            .all()
        ):
            prices_by_product[cp.product_id].append(cp)

        for item, product in matched_pairs:
            prices = prices_by_product.get(product.id, [])
            item_prices = {}
            for p in prices:
                total = float(p.price) * item.quantity
                item_prices[p.supermarket] = {
                    "unit_price": float(p.price),
                    "total": round(total, 2),
                }
                supermarket_totals[p.supermarket] += total

            item_breakdown.append({
                "item_name": item.name,
                "matched_product": product.name,
                "quantity": item.quantity,
                "matched": True,
                "prices": item_prices,
            })

    ranking = sorted(
        ({"supermarket": s, "total": round(t, 2)} for s, t in supermarket_totals.items()),
        key=lambda x: x["total"],
    )
    savings = (
        round(ranking[-1]["total"] - ranking[0]["total"], 2)
        if len(ranking) >= 2 else 0
    )

    return {
        "list_id": list_id,
        "list_name": shopping_list.name,
        "items": item_breakdown,
        "ranking": ranking,
        "savings": savings,
        "data_source": "real_prices",
    }


@admin_router.get("/status")
def scrapers_status(db: Session = Depends(get_db)):
    """Estado de las últimas ejecuciones de cada scraper."""
    now = datetime.now(timezone.utc)
    status = {}

    for sm in SUPERMARKETS:
        last_run = (
            db.query(ScraperRun)
            .filter(ScraperRun.supermarket == sm)
            .order_by(ScraperRun.started_at.desc())
            .first()
        )
        product_count = (
            db.query(func.count(CurrentPrice.id))
            .filter(CurrentPrice.supermarket == sm)
            .scalar()
        )
        latest_price = (
            db.query(CurrentPrice)
            .filter(CurrentPrice.supermarket == sm)
            .order_by(CurrentPrice.last_seen.desc())
            .first()
        )

        status[sm] = {
            "products_in_db": product_count,
            "last_scrape": last_run.started_at.isoformat() if last_run else None,
            "last_scrape_status": last_run.status if last_run else "never_run",
            "last_scrape_products": last_run.products_scraped if last_run else 0,
            "last_scrape_errors": last_run.errors if last_run else 0,
            "freshness_hours": (
                (now - latest_price.last_seen).total_seconds() / 3600
                if latest_price and latest_price.last_seen else None
            ),
        }

    return {"scrapers": status, "checked_at": now.isoformat()}
