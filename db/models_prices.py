"""
Modelos de base de datos para productos y precios reales.
"""
from sqlalchemy import (
    Column, String, DateTime, Boolean, ForeignKey, Numeric, Integer, Text,
    UniqueConstraint, Index,
)

from db.database import Base, utcnow as _utcnow
from db.models import gen_uuid


class Product(Base):
    """Catálogo maestro de productos."""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), index=True)
    brand = Column(String(100))
    image_url = Column(Text)
    unit_type = Column(String(20))     # 'kg', 'l', 'ud'
    unit_size = Column(Numeric(10, 3))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class CurrentPrice(Base):
    """Precio actual por producto+supermercado."""
    __tablename__ = "current_prices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    supermarket = Column(String(50), nullable=False, index=True)
    external_id = Column(String(100))
    price = Column(Numeric(10, 2), nullable=False)
    price_per_unit = Column(Numeric(10, 2))
    in_stock = Column(Boolean, default=True)
    product_url = Column(Text)
    last_seen = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("product_id", "supermarket", name="uq_product_supermarket"),
    )


class PriceHistory(Base):
    """Histórico de precios (para gráficos)."""
    __tablename__ = "price_history"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    supermarket = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime, default=_utcnow, index=True)

    __table_args__ = (
        Index("ix_history_product_super", "product_id", "supermarket"),
    )


class ScraperRun(Base):
    """Log de cada ejecución de un scraper."""
    __tablename__ = "scraper_runs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    supermarket = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, default=_utcnow)
    finished_at = Column(DateTime)
    products_scraped = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(20), default="running")
    error_message = Column(Text)
