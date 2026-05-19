"""
api/auth.py — Autenticación JWT, tokens opacos y lockout de logins.
"""
import hashlib
import logging
import os
import secrets
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from db.database import get_db, utcnow
from db.models import User

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

VERIFICATION_TOKEN_HOURS = 24
PASSWORD_RESET_TOKEN_MINUTES = 60

MAX_FAILED_LOGINS = 5
FAILED_WINDOW_MINUTES = 15
LOCKOUT_MINUTES = 15

_ENV = os.getenv("ENVIRONMENT", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if _ENV == "production":
        raise RuntimeError("SECRET_KEY env var es obligatoria en producción")
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("⚠️ SECRET_KEY no definida: usando valor aleatorio de desarrollo")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Contraseñas ─────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT de sesión ───────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


# ── Tokens opacos (verificación / reset) ────────────────────────────────────

def generate_opaque_token() -> str:
    """Token aleatorio seguro de 43 chars URL-safe."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash SHA-256 hex (64 chars) — para almacenar tokens en BD."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Lockout por intentos fallidos ───────────────────────────────────────────

def is_locked_out(user: User) -> bool:
    if not user.lockout_until:
        return False
    return user.lockout_until > utcnow()


def register_failed_login(user: User) -> None:
    """Suma un intento fallido y aplica lockout si procede."""
    now = utcnow()
    window_start = now - timedelta(minutes=FAILED_WINDOW_MINUTES)

    if user.last_failed_login and user.last_failed_login >= window_start:
        user.failed_login_count = (user.failed_login_count or 0) + 1
    else:
        user.failed_login_count = 1

    user.last_failed_login = now

    if user.failed_login_count >= MAX_FAILED_LOGINS:
        user.lockout_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        user.failed_login_count = 0


def reset_failed_logins(user: User) -> None:
    user.failed_login_count = 0
    user.last_failed_login = None
    user.lockout_until = None
