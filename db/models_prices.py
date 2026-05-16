"""
Modelos de base de datos para productos y precios reales.
Añadir estos modelos al archivo models.py de tu backend en Railway.
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Numeric, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from database import Base  # Tu Base existente


class Product(Base):
    """Catálogo maestro de productos."""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), index=True)
    brand = Column(String(100))
    image_url = Column(Text)
    unit_type = Column(String(20))     # 'kg', 'l', 'ud'
    unit_size = Column(Numeric(10, 3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CurrentPrice(Base):
    """Precio actual por producto+supermercado."""
    __tablename__ = "current_prices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    supermarket = Column(String(50), nullable=False)
    external_id = Column(String(100))
    price = Column(Numeric(10, 2), nullable=False)
    price_per_unit = Column(Numeric(10, 2))
    in_stock = Column(Boolean, default=True)
    product_url = Column(Text)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('product_id', 'supermarket', name='uq_product_supermarket'),
    )


class PriceHistory(Base):
    """Histórico de precios (para gráficos)."""
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    supermarket = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class ScraperRun(Base):
    """Log de cada ejecución de un scraper."""
    __tablename__ = "scraper_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supermarket = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    products_scraped = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(20), default="running")
    error_message = Column(Text)
