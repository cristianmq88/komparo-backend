"""
db/models.py — Modelos de la base de datos
"""
import uuid

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from db.database import Base, utcnow as _utcnow


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, default="Madrid")
    postal_code = Column(String, default="28001")
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    # Verificación de email
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(64), nullable=True, index=True)
    verification_expires = Column(DateTime, nullable=True)

    # Lockout por intentos fallidos
    failed_login_count = Column(Integer, default=0, nullable=False)
    last_failed_login = Column(DateTime, nullable=True)
    lockout_until = Column(DateTime, nullable=True)

    lists = relationship(
        "ShoppingList", back_populates="owner", cascade="all, delete-orphan"
    )


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    emoji = Column(String, default="🛒")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    owner = relationship("User", back_populates="lists")
    items = relationship(
        "ListItem", back_populates="shopping_list", cascade="all, delete-orphan"
    )


class ListItem(Base):
    __tablename__ = "list_items"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    list_id = Column(
        String(36), ForeignKey("shopping_lists.id"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    is_white_label = Column(Boolean, default=False)
    quantity = Column(Integer, default=1)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    shopping_list = relationship("ShoppingList", back_populates="items")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String)
    servings = Column(Integer, default=4)
    time_minutes = Column(Integer)
    difficulty = Column(String, default="media")
    category = Column(String, index=True)
    ingredients = Column(JSON)
    instructions = Column(Text)
    source = Column(String)
    created_at = Column(DateTime, default=_utcnow)


class PasswordResetToken(Base):
    """Tokens de recuperación de contraseña (hasheados, de un solo uso)."""
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
