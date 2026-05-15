"""
db/models.py — Modelos de base de datos
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(UUID, primary_key=True, default=gen_uuid)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name          = Column(String(100))
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    lists         = relationship("ShoppingList", back_populates="owner", cascade="all, delete")
    shared_lists  = relationship("ListShare", back_populates="user")


# ─────────────────────────────────────────────
# SUPERMERCADOS
# ─────────────────────────────────────────────
class Supermarket(Base):
    __tablename__ = "supermarkets"

    id            = Column(String(50), primary_key=True)   # "mercadona", "carrefour"…
    name          = Column(String(100), nullable=False)
    logo_url      = Column(String(500))
    color         = Column(String(7))                      # hex color para la UI
    website       = Column(String(200))
    scraper_class = Column(String(100))                    # nombre de la clase scraper
    is_active     = Column(Boolean, default=True)
    last_scraped  = Column(DateTime)

    products      = relationship("Product", back_populates="supermarket")


# ─────────────────────────────────────────────
# PRODUCTOS
# ─────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    supermarket_id  = Column(String(50), ForeignKey("supermarkets.id"), nullable=False)
    external_id     = Column(String(200))         # ID interno del super
    name            = Column(String(500), nullable=False)
    brand           = Column(String(200))
    category        = Column(String(100))
    subcategory     = Column(String(100))
    image_url       = Column(String(500))
    unit            = Column(String(50))          # "kg", "L", "ud", "g"
    unit_size       = Column(Float)               # tamaño de la unidad (ej: 1.5 para 1.5L)
    is_own_brand    = Column(Boolean, default=False)
    is_available    = Column(Boolean, default=True)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supermarket     = relationship("Supermarket", back_populates="products")
    prices          = relationship("Price", back_populates="product", order_by="Price.scraped_at.desc()")
    normalized      = relationship("NormalizedProduct", back_populates="products", secondary="product_mappings")

    __table_args__ = (
        UniqueConstraint("supermarket_id", "external_id", name="uq_super_product"),
        Index("ix_product_category", "category"),
        Index("ix_product_name", "name"),
    )


class Price(Base):
    """Historial de precios — una fila por scraping"""
    __tablename__ = "prices"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    product_id      = Column(UUID, ForeignKey("products.id"), nullable=False)
    price           = Column(Float, nullable=False)          # precio total
    price_per_unit  = Column(Float)                          # precio por kg/L/ud
    unit_label      = Column(String(50))                     # "€/kg", "€/L"
    is_on_sale      = Column(Boolean, default=False)
    original_price  = Column(Float)                          # precio sin oferta
    scraped_at      = Column(DateTime, default=datetime.utcnow, index=True)
    postal_code     = Column(String(10), default="28001")    # zona Madrid

    product         = relationship("Product", back_populates="prices")

    __table_args__ = (
        Index("ix_price_product_date", "product_id", "scraped_at"),
    )


# ─────────────────────────────────────────────
# PRODUCTOS NORMALIZADOS (matching cross-super)
# ─────────────────────────────────────────────
class NormalizedProduct(Base):
    """
    Agrupa productos equivalentes de distintos supermercados.
    Ej: "Leche semidesnatada 1L" → Hacendado + Auchan + Lidl Milbona
    """
    __tablename__ = "normalized_products"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    canonical_name  = Column(String(300), nullable=False)
    category        = Column(String(100))
    subcategory     = Column(String(100))

    products        = relationship("Product", back_populates="normalized", secondary="product_mappings")


class ProductMapping(Base):
    """Tabla de relación: normalized_product ↔ product"""
    __tablename__ = "product_mappings"

    normalized_id   = Column(UUID, ForeignKey("normalized_products.id"), primary_key=True)
    product_id      = Column(UUID, ForeignKey("products.id"), primary_key=True)
    confidence      = Column(Float, default=1.0)   # 0-1, qué tan seguro es el match


# ─────────────────────────────────────────────
# LISTAS DE LA COMPRA
# ─────────────────────────────────────────────
class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    owner_id        = Column(UUID, ForeignKey("users.id"), nullable=False)
    name            = Column(String(200), default="Mi lista")
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner           = relationship("User", back_populates="lists")
    items           = relationship("ListItem", back_populates="list", cascade="all, delete")
    shares          = relationship("ListShare", back_populates="list", cascade="all, delete")


class ListItem(Base):
    __tablename__ = "list_items"

    id                  = Column(UUID, primary_key=True, default=gen_uuid)
    list_id             = Column(UUID, ForeignKey("shopping_lists.id"), nullable=False)
    normalized_product_id = Column(UUID, ForeignKey("normalized_products.id"))
    custom_name         = Column(String(300))   # si el usuario escribe a mano
    quantity            = Column(Float, default=1.0)
    is_checked          = Column(Boolean, default=False)
    added_at            = Column(DateTime, default=datetime.utcnow)

    list                = relationship("ShoppingList", back_populates="items")
    normalized_product  = relationship("NormalizedProduct")


class ListShare(Base):
    """Compartir lista con otro usuario"""
    __tablename__ = "list_shares"

    id              = Column(UUID, primary_key=True, default=gen_uuid)
    list_id         = Column(UUID, ForeignKey("shopping_lists.id"), nullable=False)
    user_id         = Column(UUID, ForeignKey("users.id"), nullable=False)
    can_edit        = Column(Boolean, default=False)
    shared_at       = Column(DateTime, default=datetime.utcnow)

    list            = relationship("ShoppingList", back_populates="shares")
    user            = relationship("User", back_populates="shared_lists")

    __table_args__ = (
        UniqueConstraint("list_id", "user_id", name="uq_list_user"),
    )
