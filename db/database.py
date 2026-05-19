"""
db/database.py — Conexión a BD, esquema y semillas
"""
import logging
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """UTC naive — compatible con columnas SQLAlchemy DateTime (sin tz)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./komparo.db")

# Railway usa el esquema antiguo postgres://; SQLAlchemy requiere postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency para FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────────────────
# Migraciones ligeras: añadir columnas faltantes en tablas ya existentes.
# Sustituir por Alembic cuando el esquema crezca.
# ──────────────────────────────────────────────────────────────────────────────

_PENDING_COLUMNS = {
    "users": [
        ("email_verified", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("verification_token", "VARCHAR(64)"),
        ("verification_expires", "TIMESTAMP"),
        ("failed_login_count", "INTEGER DEFAULT 0 NOT NULL"),
        ("last_failed_login", "TIMESTAMP"),
        ("lockout_until", "TIMESTAMP"),
    ],
}


def ensure_schema_updates() -> None:
    """Añade columnas que falten en tablas existentes (idempotente)."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, columns in _PENDING_COLUMNS.items():
        if table_name not in existing_tables:
            continue
        existing = {c["name"] for c in inspector.get_columns(table_name)}
        with engine.begin() as conn:
            for col_name, col_ddl in columns:
                if col_name in existing:
                    continue
                try:
                    conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_ddl}"
                    ))
                    logger.info(f"➕ Columna añadida: {table_name}.{col_name}")
                    # Usuarios pre-existentes se asumen verificados (no romper su acceso)
                    if table_name == "users" and col_name == "email_verified":
                        conn.execute(text(
                            "UPDATE users SET email_verified = TRUE "
                            "WHERE email_verified = FALSE OR email_verified IS NULL"
                        ))
                        logger.info("✅ Usuarios pre-existentes marcados como verificados")
                except Exception as e:
                    logger.warning(
                        f"No se pudo añadir {table_name}.{col_name}: {e}"
                    )


def seed_recipes_if_empty() -> None:
    """Inserta las recetas iniciales si la tabla está vacía."""
    from db.models import Recipe
    from db.recipes_seed import RECIPES

    db = SessionLocal()
    try:
        existing = db.query(Recipe.id).first()
        if existing:
            return
        for r in RECIPES:
            db.add(Recipe(
                id=r["id"],
                title=r["title"],
                description=r.get("description"),
                image_url=r.get("image_url"),
                servings=r.get("servings", 4),
                time_minutes=r.get("time_minutes"),
                difficulty=r.get("difficulty", "media"),
                category=r.get("category"),
                ingredients=r.get("ingredients", []),
                instructions=r.get("instructions"),
            ))
        db.commit()
        logger.info(f"🌱 Sembradas {len(RECIPES)} recetas iniciales")
    except Exception as e:
        db.rollback()
        logger.warning(f"No se pudieron sembrar recetas: {e}")
    finally:
        db.close()
