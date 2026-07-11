"""
api/auth.py — Autenticación JWT
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "komparo-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

# La sesión se guarda en una cookie HttpOnly (no accesible desde JavaScript, a
# prueba de XSS). En producción (HTTPS) la cookie va con Secure; en desarrollo
# local sobre http se puede desactivar con COOKIE_SECURE=false.
COOKIE_NAME = "komparo_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() != "false"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auto_error=False: si no viene la cabecera Authorization no lanzamos error aquí,
# porque el token puede llegar también en la cookie HttpOnly.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def set_auth_cookie(response: Response, token: str) -> None:
    """Fija la cookie de sesión HttpOnly con el JWT."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Elimina la cookie de sesión (logout / baja)."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Preferimos la cabecera Authorization (clientes de API); si no viene,
    # usamos la cookie HttpOnly (navegador web).
    if not token:
        token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
