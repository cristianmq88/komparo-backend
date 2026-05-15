"""
db/database.py — Conexión a PostgreSQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Railway provee DATABASE_URL automáticamente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./komparo.db")

# Railway usa postgresql:// pero SQLAlchemy prefiere postgresql+psycopg2://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
